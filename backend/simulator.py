import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import Sample, Settings

LOCAL_TZ = ZoneInfo("Europe/Bratislava")
STEP = 300
EFFICIENCY = 0.95


def turbine_power(wind_ms: float, rated_w: float) -> float:
    points = [(0, 0), (3, 0), (5, 0.08), (8, 0.35), (10, 0.65), (12, 1), (24.99, 1)]
    if wind_ms >= 25 or wind_ms <= 3:
        return 0.0
    for (a, pa), (b, pb) in zip(points, points[1:]):
        if a <= wind_ms <= b:
            return rated_w * (pa + (pb - pa) * (wind_ms - a) / (b - a))
    return rated_w


def pv_power(settings, weather):
    if not settings.pv_enabled:
        return 0.0
    temperature_loss = 1 - max(0, weather["temperature_c"] - 25) * 0.004
    return min(settings.pv_kwp * 1000, settings.pv_kwp * weather["tilted_wm2"] * 0.86 * temperature_loss)


class Simulator:
    def __init__(self, settings: Settings, timestamp: datetime, energy: float | None = None):
        self.settings = settings
        self.timestamp = timestamp
        self.energy = settings.battery_kwh * 0.55 if energy is None else energy
        self.scenario = "sunny"

    def set_scenario(self, scenario: str):
        self.scenario = scenario
        self.energy = self.settings.battery_kwh * {"empty": 0.1, "surplus": 0.98, "outage": 0.3}.get(scenario, 0.55)

    def step(self, seeded=False, measured=None, interval_seconds=STEP, weather=None) -> Sample:
        s = self.settings
        self.timestamp += timedelta(seconds=interval_seconds)
        local = (self.timestamp - timedelta(seconds=interval_seconds / 2)).astimezone(LOCAL_TZ)
        hour = local.hour + local.minute / 60
        day = local.timetuple().tm_yday
        wave = math.sin(self.timestamp.timestamp() / 900)
        cloud = max(0, min(100, (85 if self.scenario == "cloudy" else 12) + 8 * wave))
        sun = max(0, math.sin(math.pi * (hour - 6) / 12))
        season = 0.7 + 0.3 * math.cos(2 * math.pi * (day - 172) / 365)
        latitude_factor = max(0.35, math.cos(math.radians(s.latitude - 35)))
        radiation = 1000 * sun * season * latitude_factor * (1 - cloud / 115)
        temperature = 12 + 12 * sun + 2 * wave
        wind = max(0, 5 + 2.8 * math.sin(self.timestamp.timestamp() / 5500))
        orientation = max(0.15, 0.65 + 0.35 * math.cos(math.radians(s.azimuth_deg - 180)))
        tilt = max(0.3, math.cos(math.radians(s.tilt_deg - 35)))
        if self.scenario == "surplus":
            radiation = 980  # Prezentačný zásah, nie astronomická predpoveď.
            cloud = 0
        if self.scenario in ("evening", "empty", "outage"):
            radiation *= 0.06
        pv = s.pv_kwp * radiation * orientation * tilt * 0.9 * (1 - max(0, temperature - 25) * 0.004) if s.pv_enabled else 0.0
        if weather and not s.demo_mode:
            temperature, cloud, wind, radiation = (weather[k] for k in ("temperature_c", "cloud_pct", "wind_ms", "radiation_wm2"))
            pv = pv_power(s, weather)
        if measured and s.pv_enabled:
            pv = min(measured.panel_power_w / s.pv_reference_w, 1.2) * s.pv_kwp * 1000
            if measured.temperature_c is not None:
                temperature = measured.temperature_c
        wind_power = turbine_power(wind, s.wind_kw * 1000) if s.wind_enabled else 0.0
        morning = 700 * math.exp(-((hour - 7.5) / 1.4) ** 2)
        evening = 1700 * math.exp(-((hour - 19) / 2.0) ** 2)
        load = max(50, s.base_load_w + morning + evening + 100 * wave)
        if measured:
            load += (0, 150, 500, 2000)[measured.load_stage]
        if self.scenario in ("evening", "expensive"):
            load += 2300
        if self.scenario == "surplus":
            load *= 0.6
        net = load - pv - wind_power
        battery = 0.0
        hours = interval_seconds / 3600
        minimum = s.battery_kwh * 0.1
        if s.battery_enabled:
            if net > 0:
                battery = min(net, s.battery_max_kw * 1000, max(0, self.energy - minimum) * 1000 * EFFICIENCY / hours)
                self.energy -= battery / 1000 * hours / EFFICIENCY
            else:
                charge = min(-net, s.battery_max_kw * 1000, max(0, s.battery_kwh - self.energy) * 1000 / EFFICIENCY / hours)
                battery = -charge
                self.energy += charge / 1000 * hours * EFFICIENCY
            self.energy = max(minimum, min(s.battery_kwh, self.energy))
        grid_available = self.scenario != "outage" and (measured.grid_available if measured else True)
        remaining = net - battery
        grid = remaining if grid_available else 0.0
        unserved = max(0, remaining) if not grid_available else 0.0
        curtailed = max(0, -remaining) if not grid_available else 0.0
        served = load - unserved
        voltage = 230 + 1.5 * wave if served > 0.01 else 0.0
        eta = None
        if battery > 1:
            eta = max(0, self.energy - minimum) * EFFICIENCY / (battery / 1000)
        elif battery < -1:
            eta = max(0, s.battery_kwh - self.energy) / (-battery / 1000 * EFFICIENCY)
        buy = s.offpeak_price if s.price_mode == "time_of_use" and (hour < 6 or hour >= 22) else s.buy_price
        if self.scenario == "cheap":
            buy = 0.03
        elif self.scenario == "expensive":
            buy = 0.55
        return Sample(
            timestamp=self.timestamp.isoformat(), interval_seconds=interval_seconds,
            scenario=self.scenario, seeded=seeded,
            source="hybrid" if measured else "planning" if not s.demo_mode and s.measurement_source == "planning" else "simulator",
            quality="mixed" if measured else "estimated" if not s.demo_mode and s.measurement_source == "planning" else "synthetic",
            device_id=measured.device_id if measured else None,
            panel_power_w=measured.panel_power_w if measured else None,
            illuminance_lux=measured.illuminance_lux if measured else None,
            load_w=load, served_w=served, pv_w=pv, wind_w=wind_power, grid_w=grid,
            battery_w=battery, unserved_w=unserved, curtailed_w=curtailed,
            voltage_v=voltage, current_a=served / voltage if voltage else 0,
            soc_pct=self.energy / s.battery_kwh * 100 if s.battery_enabled else None,
            battery_energy_kwh=self.energy if s.battery_enabled else None, battery_eta_hours=eta,
            temperature_c=temperature, cloud_pct=cloud, wind_ms=wind, radiation_wm2=radiation,
            grid_available=grid_available, buy_eur_kwh=buy if s.prices_enabled else None,
            sell_eur_kwh=s.sell_price if s.prices_enabled else None,
            distribution_eur_kwh=s.distribution_price if s.prices_enabled else None,
            fixed_eur_day=s.fixed_daily if s.prices_enabled else None,
        )
