import csv
import io
import math
from datetime import datetime, timedelta, timezone

from .models import Sample
from .simulator import LOCAL_TZ


def tariff_values(stamp, settings, seconds):
    buy = settings.buy_price
    if settings.price_mode == "time_of_use":
        begin, weighted = stamp - timedelta(seconds=seconds), 0.0
        while begin < stamp:
            stop = min(stamp, begin.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
            hour = begin.astimezone(LOCAL_TZ).hour
            rate = settings.offpeak_price if hour < 6 or hour >= 22 else settings.buy_price
            weighted += rate * (stop - begin).total_seconds()
            begin = stop
        buy = weighted / seconds
    return {"buy_eur_kwh": buy if settings.prices_enabled else None,
            "sell_eur_kwh": settings.sell_price if settings.prices_enabled else None,
            "distribution_eur_kwh": settings.distribution_price if settings.prices_enabled else None,
            "fixed_eur_day": settings.fixed_daily if settings.prices_enabled else None}


def reprice_samples(rows, settings):
    return [Sample.model_validate({**row, **tariff_values(datetime.fromisoformat(row["timestamp"]), settings, row["interval_seconds"])}) for row in rows]


def read_energy_csv(content, settings):
    text = content.lstrip("\ufeff").strip()
    if not text:
        raise ValueError("CSV neobsahuje žiadne intervaly.")
    delimiter = ";" if ";" in text.splitlines()[0] else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not {"timestamp", "interval_minutes", "load_kwh"} <= set(reader.fieldnames):
        raise ValueError("CSV musí mať stĺpce timestamp, interval_minutes, load_kwh a voliteľne pv_kwh.")
    samples, previous_end = [], None
    for index, row in enumerate(reader, 2):
        if index > 35041:
            raise ValueError("Jeden import môže obsahovať najviac 35 040 intervalov.")
        try:
            if None in row:
                raise ValueError("Počet hodnôt nesedí s hlavičkou CSV.")
            if any(not isinstance(row.get(key), str) or not row[key].strip() for key in ("timestamp", "interval_minutes", "load_kwh")):
                raise ValueError("Chýba čas, interval alebo spotreba.")
            stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("Čas musí obsahovať časové pásmo, napríklad +02:00.")
            stamp = stamp.astimezone(timezone.utc)
            if not 1970 <= stamp.year <= 2100:
                raise ValueError("Čas musí byť v rozsahu rokov 1970 až 2100.")
            minutes = float(row["interval_minutes"].replace(",", "."))
            load = float(row["load_kwh"].replace(",", "."))
            pv = float((row.get("pv_kwh") or "0").replace(",", "."))
            if not all(math.isfinite(x) for x in (minutes, load, pv)) or not (1 <= minutes <= 1440) or min(load, pv) < 0:
                raise ValueError("Energia musí byť nezáporná a interval od jednej minúty do jedného dňa.")
            seconds = round(minutes * 60)
            if previous_end and stamp - timedelta(seconds=seconds) < previous_end:
                raise ValueError("Intervaly musia byť zoradené a nesmú sa prekrývať.")
            load_w, pv_w = load * 3600000 / seconds, pv * 3600000 / seconds
            if max(load_w, pv_w) > 1_000_000:
                raise ValueError("Výkon presahuje povolený rozsah domácnosti.")
            samples.append(Sample(timestamp=stamp.isoformat(), interval_seconds=seconds, source="csv", quality="imported",
                                  scenario="sunny", load_w=load_w, served_w=load_w, pv_w=pv_w, wind_w=0,
                                  grid_w=load_w - pv_w, battery_w=0, unserved_w=0, curtailed_w=0,
                                  temperature_c=0, cloud_pct=0, wind_ms=0, radiation_wm2=0, grid_available=True,
                                  **tariff_values(stamp, settings, seconds)))
            previous_end = stamp
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            raise ValueError(f"Riadok {index}: {error}") from error
    if not samples:
        raise ValueError("CSV neobsahuje žiadne intervaly.")
    return samples
