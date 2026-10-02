from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Settings(StrictModel):
    configured: bool = False
    demo_mode: bool = True
    pv_enabled: bool = True
    battery_enabled: bool = True
    wind_enabled: bool = False
    weather_enabled: bool = True
    prices_enabled: bool = True
    pv_kwp: float = Field(6, ge=0.1, le=100)
    azimuth_deg: float = Field(180, ge=0, le=360)
    tilt_deg: float = Field(35, ge=0, le=90)
    latitude: float = Field(48.15, ge=-90, le=90)
    longitude: float = Field(17.11, ge=-180, le=180)
    location_name: str = Field("", max_length=120)
    location_set: bool = False
    battery_kwh: float = Field(10, ge=0.1, le=200)
    battery_max_kw: float = Field(3, ge=0.1, le=100)
    battery_capacity_mah: int = Field(1000, ge=100, le=10000)
    wind_kw: float = Field(2, ge=0.1, le=50)
    base_load_w: float = Field(600, ge=50, le=20000)
    price_mode: Literal["manual", "time_of_use"] = "manual"
    buy_price: float = Field(0.19, ge=0, le=10)
    sell_price: float = Field(0.06, ge=0, le=10)
    offpeak_price: float = Field(0.11, ge=0, le=10)
    distribution_price: float = Field(0.05, ge=0, le=10)
    fixed_daily: float = Field(0.25, ge=0, le=100)
    measurement_source: Literal["simulator", "hybrid", "planning", "csv"] = "simulator"
    pv_reference_w: float = Field(0.5, gt=0, le=20)
    weather_source: Literal["simulator", "internet"] = "internet"
    price_source: Literal["manual", "internet"] = "manual"
    supplier_markup: float = Field(0, ge=0, le=10)
    energy_vat_pct: float = Field(0, ge=0, le=100)
    ai_enabled: bool = True
    ai_model: Literal["qwen3:0.6b", "qwen3:1.7b"] = "qwen3:0.6b"

    @model_validator(mode="after")
    def mode_source(self):
        if self.measurement_source != "csv":
            self.measurement_source = "simulator" if self.demo_mode else "hybrid"
            if not self.demo_mode:
                self.weather_source = "internet"
        return self


SCENARIOS = {
    "sunny": "Slnečný deň",
    "cloudy": "Zamračenie",
    "evening": "Večerná špička",
    "empty": "Vybitá batéria",
    "surplus": "Vysoký prebytok",
    "outage": "Výpadok siete",
    "cheap": "Nízka cena energie",
    "expensive": "Vysoká cena energie",
}
Scenario = Literal["sunny", "cloudy", "evening", "empty", "surplus", "outage", "cheap", "expensive"]


class DemoCommand(StrictModel):
    scenario: Scenario | None = None
    paused: bool | None = None
    speed: Literal[1, 5, 20] | None = None
    step: bool = False


class Esp32Telemetry(StrictModel):
    device_id: str = Field("energia-esp32", min_length=1, max_length=48, pattern=r"^[a-zA-Z0-9_-]+$")
    firmware_version: str = Field("dev", min_length=1, max_length=24)
    panel_voltage_v: float = Field(ge=0, le=26)
    panel_current_a: float = Field(ge=0, le=5)
    panel_power_w: float = Field(ge=0, le=20)
    illuminance_lux: float | None = Field(default=None, ge=0, le=300000)
    temperature_c: float | None = Field(default=None, ge=-40, le=85)
    load_stage: int = Field(0, ge=0, le=3)
    grid_available: bool = True
    battery_voltage_v: float | None = Field(default=None, ge=2.5, le=4.35)
    battery_soc_pct: float | None = Field(default=None, ge=0, le=100)
    battery_charge_rate_pct_h: float | None = Field(default=None, ge=-1000, le=1000)

    @model_validator(mode="after")
    def battery_pair(self):
        if (self.battery_voltage_v is None) != (self.battery_soc_pct is None):
            raise ValueError("Batéria musí poslať napätie aj stav nabitia, alebo obe hodnoty vynechať.")
        if self.battery_charge_rate_pct_h is not None and self.battery_soc_pct is None:
            raise ValueError("Rýchlosť zmeny SOC vyžaduje meranie batérie.")
        return self


class Sample(StrictModel):
    timestamp: str
    interval_seconds: int = Field(300, gt=0)
    source: Literal["simulator", "hybrid", "planning", "csv"] = "simulator"
    quality: Literal["synthetic", "mixed", "estimated", "imported"] = "synthetic"
    device_id: str | None = None
    panel_power_w: float | None = Field(default=None, ge=0)
    illuminance_lux: float | None = Field(default=None, ge=0)
    scenario: Scenario
    seeded: bool = False
    load_w: float = Field(ge=0)
    served_w: float = Field(ge=0)
    pv_w: float = Field(ge=0)
    wind_w: float = Field(ge=0)
    grid_w: float
    battery_w: float
    unserved_w: float = Field(ge=0)
    curtailed_w: float = Field(ge=0)
    voltage_v: float | None = Field(default=None, ge=0)
    current_a: float | None = Field(default=None, ge=0)
    soc_pct: float | None = Field(default=None, ge=0, le=100)
    battery_energy_kwh: float | None = None
    battery_eta_hours: float | None = None
    battery_voltage_v: float | None = Field(default=None, ge=2.5, le=4.35)
    battery_charge_rate_pct_h: float | None = Field(default=None, ge=-1000, le=1000)
    price_source: Literal["manual", "internet"] = "manual"
    temperature_c: float
    cloud_pct: float = Field(ge=0, le=100)
    wind_ms: float = Field(ge=0)
    radiation_wm2: float = Field(ge=0)
    grid_available: bool
    buy_eur_kwh: float | None = None
    sell_eur_kwh: float | None = None
    distribution_eur_kwh: float | None = None
    fixed_eur_day: float | None = None

    @model_validator(mode="after")
    def balanced(self):
        residual = self.pv_w + self.wind_w + self.grid_w + self.battery_w - self.served_w - self.curtailed_w
        if abs(residual) > 0.01 or abs(self.load_w - self.served_w - self.unserved_w) > 0.01:
            raise ValueError("Energetická bilancia nesedí")
        return self


class WeatherPoint(StrictModel):
    timestamp: str
    temperature_c: float = Field(ge=-100, le=70)
    cloud_pct: float = Field(ge=0, le=100)
    wind_ms: float = Field(ge=0, le=150)
    radiation_wm2: float = Field(ge=0, le=2000)
    tilted_wm2: float = Field(ge=0, le=2500)
    precipitation_mm: float = Field(0, ge=0, le=1000)
    weather_code: int = Field(0, ge=0, le=99)


class CsvImport(StrictModel):
    content: str = Field(min_length=10, max_length=3_000_000)


class ChatMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1800)


class AssistantRequest(StrictModel):
    question: str = Field(min_length=1, max_length=1200)
    history: list[ChatMessage] = Field(default_factory=list, max_length=6)


# Only application configuration is editable; telemetry and device credentials are never tools.
CHAT_SETTINGS = {
    "demo_mode": "Demo režim", "prices_enabled": "Modul cien",
    "price_source": "Zdroj ceny", "price_mode": "Tarifný režim",
    "buy_price": "Nákup (€/kWh)", "sell_price": "Výkup (€/kWh)",
    "offpeak_price": "Nízka tarifa (€/kWh)", "distribution_price": "Distribúcia (€/kWh)",
    "fixed_daily": "Fixný poplatok (€/deň)", "supplier_markup": "Prirážka (€/kWh)",
    "energy_vat_pct": "DPH energie (%)", "pv_enabled": "Fotovoltaika",
    "battery_enabled": "Batéria", "wind_enabled": "Veterná turbína",
    "weather_enabled": "Počasie", "weather_source": "Zdroj počasia",
    "pv_kwp": "Výkon FV (kWp)", "battery_capacity_mah": "Kapacita článku (mAh)",
    "battery_kwh": "Kapacita demo batérie (kWh)", "base_load_w": "Základná spotreba (W)",
}


class AssistantApplyRequest(StrictModel):
    token: str = Field(min_length=20, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
