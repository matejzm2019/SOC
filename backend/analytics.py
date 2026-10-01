from datetime import datetime, timedelta
from math import sqrt


def recommendations(sample, settings):
    items = []
    if not sample.grid_available:
        items.append({"title": "Ostrovný režim", "text": "Sieť je odpojená. Sledujte nepokrytú spotrebu a obmedzte virtuálne záťaže.", "kind": "warning"})
    if sample.unserved_w > 1:
        items.append({"title": "Nedostatok výkonu", "text": f"Nepokrytý odber je {sample.unserved_w / 1000:.2f} kW. Tento odber sa nezapočítava ako dodaná energia.", "kind": "warning"})
    if sample.grid_w < -100:
        items.append({"title": "Využite prebytok", "text": f"Do siete odchádza {-sample.grid_w / 1000:.2f} kW. V simulácii môžete presunúť spotrebu do tohto intervalu.", "kind": "good"})
    if settings.battery_enabled and sample.soc_pct <= 15:
        items.append({"title": "Batéria na rezerve", "text": f"SOC je {sample.soc_pct:.0f} %. Vybíjanie sa zastaví na 10 %.", "kind": "warning"})
    if settings.prices_enabled and sample.buy_eur_kwh >= 0.4:
        items.append({"title": "Drahý nákup", "text": "Scenár má vysokú nákupnú cenu. Odloženie flexibilnej spotreby môže znížiť náklady.", "kind": "warning"})
    if settings.prices_enabled and sample.buy_eur_kwh <= 0.05:
        items.append({"title": "Lacné tarifné okno", "text": "Porovnajte presun spotreby do tohto intervalu. MVP batériu zo siete automaticky nenabíja.", "kind": "good"})
    if not items:
        items.append({"title": "Energetická bilancia v rovnováhe", "text": "Výroba, batéria a sieť pokrývajú aktuálnu spotrebu. Sledujte vývoj počas celého dňa.", "kind": "good"})
    return {"engine": "rules", "label": "Pravidlové zhrnutie · bez LLM", "items": items}


def forecast(rows):
    if len(rows) < 288:
        return {"available": False, "reason": "Baseline vyžaduje aspoň 24 hodín päťminútových dát."}
    last_day = rows[-288:]
    end = datetime.fromisoformat(rows[-1]["timestamp"])
    points = []
    for hour in range(24):
        group = last_day[hour * 12:(hour + 1) * 12]
        points.append({"timestamp": (end + timedelta(hours=hour + 1)).isoformat(),
                       **{key: sum(r[key] for r in group) / 12 for key in ("load_w", "pv_w", "wind_w")}})
    metrics = None
    if len(rows) >= 576:
        metrics = {}
        for key in ("load_w", "pv_w", "wind_w"):
            errors = [a[key] - b[key] for a, b in zip(rows[-288:], rows[-576:-288])]
            metrics[key] = {"mae_w": sum(abs(e) for e in errors) / 288,
                            "rmse_w": sqrt(sum(e * e for e in errors) / 288)}
    return {"available": True, "model": "Sezónny naivný model (t − 24 h)", "points": points,
            "metrics": metrics, "synthetic": True,
            "note": "Opakuje predchádzajúci deň; nezohľadňuje budúce počasie ani zmenu scenára. Hodnotenie vyžaduje 48 h dát."}
