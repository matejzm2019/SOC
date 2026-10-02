import asyncio
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from time import monotonic

import httpx

from .models import WeatherPoint

UTC = timezone.utc
VARIABLES = "temperature_2m,cloud_cover,wind_speed_10m,shortwave_radiation,global_tilted_irradiance,precipitation,weather_code"


def weather_description(code):
    if code == 0:
        return "Jasno"
    if code in (1, 2):
        return "Polojasno"
    if code == 3:
        return "Zamračené"
    if code in (45, 48):
        return "Hmla"
    if code >= 95:
        return "Búrky"
    if code in (71, 73, 75, 77, 85, 86):
        return "Sneženie"
    return "Dážď alebo mrholenie"


def weather_key(settings):
    return [round(settings.latitude, 3), round(settings.longitude, 3), settings.tilt_deg, settings.azimuth_deg]


def normalize_point(values, timestamp):
    point = WeatherPoint(
        timestamp=datetime.fromtimestamp(timestamp, UTC).isoformat(),
        temperature_c=values["temperature_2m"], cloud_pct=values["cloud_cover"],
        wind_ms=values["wind_speed_10m"], radiation_wm2=values["shortwave_radiation"],
        tilted_wm2=values["global_tilted_irradiance"], precipitation_mm=values["precipitation"],
        weather_code=values["weather_code"],
    ).model_dump()
    return {**point, "condition": weather_description(point["weather_code"])}


class WeatherService:
    def __init__(self, client, storage):
        self.client, self.storage = client, storage
        self.snapshot = None
        try:
            cached = storage.cache_get("weather")
            if cached:
                fetched = datetime.fromisoformat(cached["fetched_at"])
                if fetched.tzinfo is None or fetched > datetime.now(UTC):
                    raise ValueError("Invalid cache time")
                for point in [cached["current"], *cached["hourly"]]:
                    WeatherPoint.model_validate({k: point[k] for k in WeatherPoint.model_fields})
                    stamp = datetime.fromisoformat(point["timestamp"])
                    if stamp.tzinfo is None:
                        raise ValueError("Invalid weather time")
                self.snapshot = cached
        except (ValueError, KeyError, TypeError):
            pass
        self.error = None
        self.locations = {}
        self.lock = asyncio.Lock()

    def view(self, settings):
        active = settings.weather_source == "internet" and settings.location_set
        if not active:
            return {"available": False, "stale": False, "source": settings.weather_source,
                    "error": None if settings.location_set else "Vyberte mesto alebo povoľte polohu."}
        valid = self.snapshot and self.snapshot.get("key") == weather_key(settings)
        age = (datetime.now(UTC) - datetime.fromisoformat(self.snapshot["fetched_at"])).total_seconds() if valid else None
        observation_age = (datetime.now(UTC) - datetime.fromisoformat(self.snapshot["current"]["timestamp"])).total_seconds() if valid else None
        return {"available": bool(valid), "stale": age is not None and (age > 1800 or abs(observation_age) > 2700),
                "source": "Open-Meteo", "error": self.error, "age_seconds": age,
                **({k: v for k, v in self.snapshot.items() if k != "key"} if valid else {})}

    async def refresh(self, settings):
        async with self.lock:
            await self._refresh(settings)

    async def _refresh(self, settings):
        if settings.weather_source != "internet" or not settings.location_set:
            return
        current = self.view(settings)
        if current["available"] and not current["stale"] and current["age_seconds"] < 600:
            return
        params = {"latitude": round(settings.latitude, 3), "longitude": round(settings.longitude, 3),
                  "current": VARIABLES, "hourly": VARIABLES, "forecast_days": 3,
                  "timezone": "UTC", "timeformat": "unixtime", "wind_speed_unit": "ms",
                  "tilt": settings.tilt_deg, "azimuth": settings.azimuth_deg - 180}
        try:
            response = await self.client.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            current_point = normalize_point(data["current"], data["current"]["time"])
            hourly = data["hourly"]
            points = [normalize_point({name: hourly[name][i] for name in VARIABLES.split(",")}, stamp)
                      for i, stamp in enumerate(hourly["time"])][:72]
            if len(points) < 24:
                raise ValueError("Missing forecast")
            if any(datetime.fromisoformat(b["timestamp"]) - datetime.fromisoformat(a["timestamp"]) != timedelta(hours=1) for a, b in zip(points, points[1:])):
                raise ValueError("Invalid forecast intervals")
            snapshot = {"key": weather_key(settings), "fetched_at": datetime.now(UTC).isoformat(),
                        "current": current_point, "hourly": points}
            self.storage.cache_put("weather", snapshot)
            self.snapshot, self.error = snapshot, None
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, OverflowError, sqlite3.Error):
            self.error = "Počasie sa nepodarilo aktualizovať. Posledné dostupné údaje zostávajú označené časom aktualizácie."

    async def run(self, engine):
        while True:
            await self.refresh(engine.settings)
            await asyncio.sleep(60)

    async def search(self, query):
        key = query.strip().casefold()
        cached = self.locations.get(key)
        if cached and monotonic() - cached[0] < 86400:
            return cached[1]
        response = await self.client.get("https://geocoding-api.open-meteo.com/v1/search",
                                         params={"name": query.strip(), "count": 5, "language": "sk", "format": "json"}, timeout=10)
        response.raise_for_status()
        locations = [{"name": str(item["name"])[:80], "region": str(item.get("admin1", ""))[:80],
                      "country": str(item.get("country", ""))[:80],
                      "latitude": round(float(item["latitude"]), 3), "longitude": round(float(item["longitude"]), 3)}
                     for item in response.json().get("results", [])[:5]]
        if any(not math.isfinite(p["latitude"]) or not math.isfinite(p["longitude"]) or abs(p["latitude"]) > 90 or abs(p["longitude"]) > 180 for p in locations):
            raise ValueError("Invalid location")
        if len(self.locations) >= 100:
            self.locations.pop(next(iter(self.locations)))
        self.locations[key] = (monotonic(), locations)
        return locations
