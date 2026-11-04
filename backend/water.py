"""Water commands are timed leases; the ESP enforces independent local interlocks."""
from time import monotonic
from typing import Literal
from pydantic import Field
from fastapi import HTTPException
from .models import StrictModel


class WaterConfig(StrictModel):
    enabled: bool = False
    max_run_seconds: int = Field(15, ge=2, le=60)
    filter_service_minutes: int = Field(60, ge=1, le=10000)


class WaterAction(StrictModel):
    action: Literal["manual", "auto", "stop", "reset", "filter_replaced"]


class WaterController:
    def __init__(self, storage):
        self.storage = storage
        saved = storage.cache_get("water_settings") or {}
        self.config = WaterConfig(**saved)
        self.mode = "off"
        self.started = None
        self.blocked = None
        self.last_tick = monotonic()
        self.service_seconds = float(storage.cache_get("water_service_seconds") or 0)
        self.persist_at = monotonic()
        self.reset_pending = False
        self.demo_until = None
        self.demo_service_seconds = 0
        self.demo_source_ok = True
        self.demo_full = False
        self.demo_leak = False

    def configure(self, value):
        self.config = value
        self.stop()
        self.storage.cache_put("water_settings", value.model_dump())

    def stop(self):
        self.mode, self.started, self.demo_until = "off", None, None

    def conditions(self, telemetry, online):
        if not online or telemetry is None or telemetry.water is None:
            return "link_lost"
        w = telemetry.water
        if not telemetry.grid_available:
            return "main_lost"
        if w.leak_detected:
            return "leak"
        if not w.source_ok:
            return "source_empty"
        if w.target_low and w.target_full:
            return "sensor_conflict"
        if w.fault != "none":
            return w.fault
        return None

    def action(self, value, settings, telemetry, online):
        now = monotonic()
        if value.action == "stop":
            self.stop()
            return
        if value.action == "filter_replaced":
            self.service_seconds = 0
            self.storage.cache_put("water_service_seconds", 0)
            return
        if value.action == "reset":
            self.stop()
            self.blocked = None
            self.reset_pending = True
            return
        if settings.measurement_source == "csv":
            raise HTTPException(409, "Vodný okruh nie je dostupný pri CSV histórii.")
        if not settings.demo_mode:
            if not self.config.enabled:
                raise HTTPException(409, "Najprv povoľte zapojený vodný okruh v jeho nastaveniach.")
            fault = self.conditions(telemetry, online)
            if fault or self.blocked:
                raise HTTPException(409, "Čerpadlo blokované: " + (fault or self.blocked))
            if telemetry.water.target_full:
                raise HTTPException(409, "Cieľová nádrž je plná.")
        self.mode = value.action
        self.started = None
        if settings.demo_mode:
            self.demo_until = now + min(self.config.max_run_seconds, 8)

    def command(self, telemetry, online, settings):
        now = monotonic()
        desired = False
        if not settings.demo_mode and self.config.enabled and self.mode != "off":
            fault = self.conditions(telemetry, online)
            if fault:
                self.blocked = fault
                self.stop()
            elif not self.blocked:
                w = telemetry.water
                if w.target_full:
                    if self.mode == "manual":
                        self.stop()
                    else:
                        self.started = None
                elif self.mode == "manual" or w.target_low or self.started is not None:
                    if self.started is None:
                        self.started = now
                    if now - self.started >= self.config.max_run_seconds:
                        self.blocked = "timeout"
                        self.stop()
                    else:
                        desired = True
        reset = self.reset_pending
        self.reset_pending = False
        return {"pump_on": desired, "lease_ms": 1500,
                "max_run_ms": self.config.max_run_seconds * 1000, "reset_fault": reset}

    def tick(self, settings, telemetry, online):
        now = monotonic()
        dt = min(max(0, now-self.last_tick), 2)
        self.last_tick = now
        if settings.demo_mode:
            if self.demo_until is not None and now < self.demo_until:
                self.demo_service_seconds += dt
        elif online and telemetry and telemetry.water and telemetry.water.pump_running:
            self.service_seconds += dt
        if now-self.persist_at >= 30:
            self.storage.cache_put("water_service_seconds", self.service_seconds)
            self.persist_at = now

    def view(self, settings, telemetry, online):
        now = monotonic()
        if settings.demo_mode:
            running = self.demo_until is not None and now < self.demo_until
            fault = None
            source, low, full, leak = True, not self.demo_full, self.demo_full, False
            origin = "demo"
        else:
            fault = self.conditions(telemetry, online)
            w = telemetry.water if online and telemetry else None
            running = bool(w and w.pump_running)
            source, low, full, leak = (w.source_ok, w.target_low, w.target_full, w.leak_detected) if w else (None, None, None, None)
            origin = telemetry.telemetry_origin if w else "offline"
        return {"config": self.config, "mode": self.mode, "origin": origin,
                "pump_running": running, "source_ok": source, "target_low": low,
                "target_full": full, "leak_detected": leak,
                "fault": self.blocked or fault, "service_seconds": round(self.demo_service_seconds if settings.demo_mode else self.service_seconds, 1),
                "service_due": (self.demo_service_seconds if settings.demo_mode else self.service_seconds) >= self.config.filter_service_minutes*60}
