import asyncio
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from time import monotonic

import httpx

from .simulator import LOCAL_TZ


class PriceService:
    def __init__(self, client, storage):
        self.client, self.storage = client, storage
        self.snapshot, self.error, self.attempted_at = None, None, -60
        self.points = []
        self.lock = asyncio.Lock()
        try:
            cached = storage.cache_get("prices:SK")
            if cached:
                points = self.parse(cached["data"])
                fetched = datetime.fromisoformat(cached["fetched_at"])
                if fetched.tzinfo is None or fetched > datetime.now(timezone.utc):
                    raise ValueError("Invalid cache time")
                self.snapshot = cached
                self.points = points
        except (ValueError, TypeError, KeyError, OverflowError):
            pass

    @staticmethod
    def parse(data):
        stamps, prices = data["unix_seconds"], data["price"]
        if not isinstance(data["unit"], str) or data["unit"].replace(" ", "") != "EUR/MWh" or len(stamps) != len(prices) or not 2 <= len(stamps) <= 400:
            raise ValueError("Invalid price units or intervals")
        points = []
        for i, stamp in enumerate(stamps):
            end = stamps[i + 1] if i + 1 < len(stamps) else stamp + stamps[-1] - stamps[-2]
            rate = float(prices[i]) / 1000
            if not math.isfinite(rate) or not -5 <= rate <= 10 or not 0 < end - stamp <= 3600:
                raise ValueError("Invalid price interval")
            points.append({"start": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                           "end": datetime.fromtimestamp(end, timezone.utc).isoformat(), "eur_kwh": rate})
        return points

    def quote(self, end, seconds, settings):
        if not self.snapshot:
            return None
        if datetime.now(timezone.utc) - datetime.fromisoformat(self.snapshot["fetched_at"]) > timedelta(hours=36):
            return None
        start, covered, total = end - timedelta(seconds=seconds), 0, 0
        for point in self.points:
            overlap = (min(end,datetime.fromisoformat(point["end"])) - max(start,datetime.fromisoformat(point["start"]))).total_seconds()
            if overlap > 0:
                covered += overlap
                total += point["eur_kwh"] * overlap
        if abs(covered - seconds) > .01:
            return None
        return (total / seconds + settings.supplier_markup) * (1 + settings.energy_vat_pct / 100)

    def view(self, settings):
        if not settings.prices_enabled or settings.price_source != "internet":
            return {"available": False, "source": "manual", "error": None}
        now = datetime.now(timezone.utc)
        rate = self.quote(now, 1, settings)
        age = (now - datetime.fromisoformat(self.snapshot["fetched_at"])).total_seconds() if self.snapshot else None
        return {"available": rate is not None, "source": "Energy-Charts · SK", "buy_eur_kwh": rate,
                "stale": age is not None and age > 1800, "fetched_at": self.snapshot["fetched_at"] if self.snapshot else None,
                "error": self.error or ("Pre aktuálny interval nie je dostupná internetová cena." if rate is None else None),
                "points": [p for p in self.points if datetime.fromisoformat(p["end"]) > now][:8],
                "license_info": self.snapshot["data"].get("license_info", "") if self.snapshot else ""}

    async def refresh(self, settings):
        if not settings.prices_enabled or settings.price_source != "internet":
            return
        async with self.lock:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(self.snapshot["fetched_at"])).total_seconds() if self.snapshot else None
            if age is not None and age < 1800 and self.quote(datetime.now(timezone.utc),1,settings) is not None:
                return
            if monotonic() - self.attempted_at < 60:
                return
            self.attempted_at = monotonic()
            today = datetime.now(LOCAL_TZ).replace(hour=0,minute=0,second=0,microsecond=0)
            try:
                response = await self.client.get("https://api.energy-charts.info/price", timeout=15,
                    params={"bzn":"SK", "start":(today-timedelta(days=1)).isoformat(), "end":(today+timedelta(days=2)).isoformat()})
                response.raise_for_status()
                data = response.json()
                points = self.parse(data)
                snapshot = {"data":data,"fetched_at":datetime.now(timezone.utc).isoformat()}
                self.storage.cache_put("prices:SK",snapshot)
                self.snapshot, self.points, self.error = snapshot, points, None
            except (httpx.HTTPError, ValueError, TypeError, KeyError, OverflowError, sqlite3.Error):
                self.error = "Cenu sa nepodarilo obnoviť. Použijem dostupný platný interval z cache; cenu si nevymýšľam."

    async def run(self, engine):
        while True:
            await self.refresh(engine.settings)
            await asyncio.sleep(60)
