from datetime import datetime, timedelta, timezone
from math import sqrt

from .simulator import LOCAL_TZ, Simulator, pv_power, turbine_power


def recommendations(sample, settings):
    items = []
    if not sample.grid_available:
        items.append({"title": "Ostrovný režim", "text": "Sieť je odpojená. Sledujte nepokrytú spotrebu a obmedzte virtuálne záťaže.", "kind": "warning"})
    if sample.unserved_w > 1:
        items.append({"title": "Nedostatok výkonu", "text": f"Nepokrytý odber je {sample.unserved_w / 1000:.2f} kW. Tento odber sa nezapočítava ako dodaná energia.", "kind": "warning"})
    if sample.grid_w < -100:
        context = "Bilancia importovaného intervalu ukazuje" if sample.source == "csv" else "Model ukazuje" if sample.source == "planning" else "Do siete odchádza"
        items.append({"title": "Využite prebytok", "text": f"{context} prebytok {-sample.grid_w / 1000:.2f} kW. Porovnajte podobné intervaly pri plánovaní flexibilnej spotreby.", "kind": "good"})
    if settings.battery_enabled and sample.soc_pct is not None and sample.soc_pct <= 15:
        text = f"SOC je {sample.soc_pct:.0f} %. Nabíjanie malého článku riadi solárna nabíjačka." if sample.source == "hybrid" else f"SOC je {sample.soc_pct:.0f} %. Vybíjanie modelu sa zastaví na 10 %."
        items.append({"title": "Batéria na rezerve", "text": text, "kind": "warning"})
    if settings.prices_enabled and sample.buy_eur_kwh is not None and sample.buy_eur_kwh >= 0.4:
        items.append({"title": "Drahý nákup", "text": "V tomto intervale je vysoká nákupná cena. Odloženie flexibilnej spotreby môže znížiť náklady.", "kind": "warning"})
    if settings.prices_enabled and sample.buy_eur_kwh is not None and sample.buy_eur_kwh <= 0.05:
        items.append({"title": "Lacné tarifné okno", "text": "Porovnajte presun spotreby do podobného intervalu. Aplikácia batériu zo siete automaticky nenabíja.", "kind": "good"})
    if not items:
        text = "Modelovaná spotreba je pokrytá. Fyzické ESP a svetlá napája laboratórny zdroj; solárna batéria má samostatný okruh." if sample.source == "hybrid" else "Výroba, batéria a sieť pokrývajú aktuálnu spotrebu. Sledujte vývoj počas celého dňa."
        items.append({"title": "Energetická bilancia v rovnováhe", "text": text, "kind": "good"})
    return {"engine": "rules", "label": "Pravidlové zhrnutie · bez LLM", "items": items}


def hourly_profile(rows, end):
    start = end - timedelta(days=1)
    bins = [{"seconds": 0, "load_w": 0, "pv_w": 0, "wind_w": 0} for _ in range(24)]
    for row in rows:
        stamp = datetime.fromisoformat(row["timestamp"])
        begin = stamp - timedelta(seconds=row["interval_seconds"])
        if row["interval_seconds"] > 3600 and stamp > start and begin < end:
            return None
        begin, finish = max(start, begin), min(end, stamp)
        while begin < finish:
            index = min(23, int((begin - start).total_seconds() // 3600))
            stop = min(finish, start + timedelta(hours=index + 1))
            seconds = (stop - begin).total_seconds()
            bins[index]["seconds"] += seconds
            for key in ("load_w", "pv_w", "wind_w"):
                bins[index][key] += row[key] * seconds
            begin = stop
    if any(abs(b["seconds"] - 3600) > .1 for b in bins):
        return None
    return [{key: b[key] / 3600 for key in ("load_w", "pv_w", "wind_w")} for b in bins]


def forecast(rows):
    if not rows:
        return {"available": False, "reason": "Predikcia spotreby potrebuje súvislých 24 hodín dát s intervalmi najviac jednu hodinu."}
    end = datetime.fromisoformat(rows[-1]["timestamp"])
    last_day = hourly_profile(rows, end)
    if last_day is None:
        return {"available": False, "reason": "Predikcia spotreby potrebuje súvislých 24 hodín dát s intervalmi najviac jednu hodinu."}
    points = [{"timestamp": (end + timedelta(hours=hour + 1)).isoformat(), **point} for hour, point in enumerate(last_day)]
    metrics = None
    previous = hourly_profile(rows, end - timedelta(days=1))
    if previous:
        metrics = {}
        for key in ("load_w", "pv_w", "wind_w"):
            errors = [a[key] - b[key] for a, b in zip(last_day, previous)]
            metrics[key] = {"mae_w": sum(abs(e) for e in errors) / 24,
                            "rmse_w": sqrt(sum(e * e for e in errors) / 24)}
    return {"available": True, "model": "Sezónny naivný model (t − 24 h)", "points": points,
            "metrics": metrics, "synthetic": any(r["quality"] != "imported" for r in rows),
            "note": "Opakuje predchádzajúci deň; nezohľadňuje budúce počasie ani zmenu scenára. Hodnotenie vyžaduje 48 h dát."}


def prediction(settings, weather, rows):
    baseline = forecast(rows)
    if settings.demo_mode or not weather.get("available") or weather.get("stale"):
        return baseline
    now = datetime.now(timezone.utc)
    hours = [p for p in weather["hourly"] if datetime.fromisoformat(p["timestamp"]) > now][:24]
    if len(hours) < 24:
        return baseline
    load_by_hour = {datetime.fromisoformat(p["timestamp"]).astimezone(LOCAL_TZ).hour: p["load_w"]
                    for p in baseline.get("points", [])}
    points = []
    for weather_point in hours:
        stamp = datetime.fromisoformat(weather_point["timestamp"])
        assumed = Simulator(settings, stamp - timedelta(hours=1)).step(interval_seconds=3600, weather=weather_point).load_w
        points.append({"timestamp": weather_point["timestamp"], "load_w": load_by_hour.get(stamp.astimezone(LOCAL_TZ).hour, assumed),
                       "pv_w": pv_power(settings, weather_point),
                       "wind_w": turbine_power(weather_point["wind_ms"], settings.wind_kw * 1000) if settings.wind_enabled else 0})
    return {"available": True, "model": "FV: meteorologický fyzikálny model · spotreba: " + ("predchádzajúci deň" if baseline["available"] else "zadaný profil domácnosti"),
            "points": points, "metrics": {"load_w": baseline["metrics"]["load_w"]} if baseline.get("metrics") else None, "synthetic": settings.measurement_source != "csv",
            "note": "Výroba je odhad podľa predpovede Open-Meteo a parametrov panelov. Spotreba opakuje posledný deň alebo používa zadaný profil. Nejde o meranie ani záruku budúcej výroby.",
            "weather_based": True, "load_assumed": not baseline["available"]}
