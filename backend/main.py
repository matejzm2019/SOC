import asyncio
import csv
import io
import logging
import os
import secrets
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .analytics import forecast, recommendations
from .models import DemoCommand, Esp32Telemetry, SCENARIOS, Settings
from .simulator import Simulator
from .storage import Storage

ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, path, device_key="test-device-key"):
        self.storage = Storage(path)
        self.settings = self.storage.settings()
        self.lock = asyncio.Lock()
        self.paused = True
        self.speed = 1
        self.error = None
        self.device_key = device_key
        self.device_telemetry = None
        self.device_received_at = None
        self.run_id = self.storage.latest_run()
        latest = self.storage.latest(self.run_id) if self.run_id else None
        if latest:
            self.sample = latest
            self.simulator = Simulator(self.settings, datetime.fromisoformat(latest.timestamp), latest.battery_energy_kwh)
            self.simulator.scenario = latest.scenario
        else:
            self.reset(self.settings)

    def reset(self, settings):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        if settings.demo_mode:
            end = now.replace(hour=10, minute=0, second=0)
            simulator = Simulator(settings, end - timedelta(days=1))
            samples = [simulator.step(seeded=True) for _ in range(288)]
        else:
            simulator = Simulator(settings, now - timedelta(seconds=1))
            samples = [simulator.step(seeded=True, interval_seconds=1)]
        run_id = self.storage.new_run(settings, samples)
        self.settings, self.simulator, self.run_id = settings, simulator, run_id
        self.sample = samples[-1]
        self.paused = True
        self.error = None

    def device_status(self):
        age = ((datetime.now(timezone.utc) - self.device_received_at).total_seconds()
               if self.device_received_at else None)
        return {"online": age is not None and age <= 5, "age_seconds": age,
                "last_seen": self.device_received_at.isoformat() if self.device_received_at else None,
                "telemetry": self.device_telemetry}

    def tick(self):
        timestamp, energy = self.simulator.timestamp, self.simulator.energy
        try:
            measured = None
            if self.settings.measurement_source == "hybrid":
                status = self.device_status()
                if not status["online"]:
                    raise RuntimeError("ESP32 neposlalo platné meranie za posledných 10 sekúnd")
                measured = self.device_telemetry
            interval = 300 if self.settings.demo_mode else 1
            sample = self.simulator.step(measured=measured, interval_seconds=interval)
            self.storage.save(self.run_id, [sample])
        except Exception:
            self.simulator.timestamp, self.simulator.energy = timestamp, energy
            raise
        self.sample = sample
        self.error = None

    async def run(self):
        while True:
            await asyncio.sleep(1 / self.speed if self.settings.demo_mode else 1)
            async with self.lock:
                if not self.paused:
                    try:
                        self.tick()
                    except Exception:
                        logger.exception("Simulátor bol pozastavený")
                        self.paused = True
                        self.error = "Chyba výpočtu alebo ukladania. Simulácia je pozastavená; skontrolujte log servera."

    def state(self):
        return {"settings": self.settings, "sample": self.sample, "device": self.device_status(),
                "demo": {"enabled": self.settings.demo_mode, "scenario": self.simulator.scenario,
                         "paused": self.paused, "speed": self.speed,
                         "step_seconds": 300 if self.settings.demo_mode else 1,
                         "run_id": self.run_id, "error": self.error},
                "scenarios": SCENARIOS, "summary": recommendations(self.sample, self.settings)}


def device_key(path):
    configured = os.environ.get("SOC_DEVICE_KEY")
    if configured:
        return configured
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_urlsafe(24), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


def create_app(database=None, esp32_key=None):
    @asynccontextmanager
    async def lifespan(app):
        engine = Engine(Path(database or os.environ.get("SOC_DATABASE", ROOT / "data" / "energy.sqlite3")),
                        esp32_key or device_key(ROOT / "data" / "device_key.txt"))
        app.state.engine = engine
        task = asyncio.create_task(engine.run())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        engine.storage.connection.close()

    app = FastAPI(title="Energia", version="0.4.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        if request.method in ("PUT", "POST", "DELETE", "PATCH"):
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                return Response("Cross-origin write rejected", status_code=403)
            if "application/json" not in request.headers.get("content-type", ""):
                return Response("JSON required", status_code=415)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    async def health(request: Request):
        e = request.app.state.engine
        e.storage.connection.execute("SELECT 1").fetchone()
        return {"status": "degraded" if e.error else "ok",
                "mode": "demo" if e.settings.demo_mode else "monitor", "version": "0.4.0"}

    @app.get("/api/state")
    async def state(request: Request):
        e = request.app.state.engine
        async with e.lock:
            return e.state()

    @app.post("/api/device/telemetry")
    async def ingest(value: Esp32Telemetry, request: Request):
        e = request.app.state.engine
        if not secrets.compare_digest(request.headers.get("x-device-key", ""), e.device_key):
            raise HTTPException(401, "Neplatný kľúč zariadenia")
        async with e.lock:
            e.device_telemetry = value
            e.device_received_at = datetime.now(timezone.utc)
            return {"accepted": True, "server_time": e.device_received_at.isoformat()}

    @app.put("/api/settings")
    async def settings(value: Settings, request: Request):
        e = request.app.state.engine
        async with e.lock:
            e.reset(value.model_copy(update={"configured": True}))
            return e.state()

    @app.post("/api/demo")
    async def demo(command: DemoCommand, request: Request):
        e = request.app.state.engine
        async with e.lock:
            if not e.settings.demo_mode and (command.scenario or command.speed or command.step):
                raise HTTPException(409, "Scenáre, zrýchlenie a ručný krok vyžadujú DEMO MODE")
            if command.step and command.paused is False:
                raise HTTPException(422, "Samostatný krok vyžaduje pauzu")
            if command.scenario:
                e.simulator.set_scenario(command.scenario)
            if command.paused is not None:
                e.paused = command.paused
            if command.speed is not None:
                e.speed = command.speed
            if command.step:
                e.paused = True
            if command.step or command.scenario:
                try:
                    e.tick()
                except RuntimeError as error:
                    raise HTTPException(409, str(error)) from error
            return e.state()

    @app.get("/api/history")
    async def history(request: Request, period: Literal["day", "week", "month", "all"] = "day"):
        e = request.app.state.engine
        async with e.lock:
            return e.storage.history(e.run_id, period)

    @app.get("/api/forecast")
    async def prediction(request: Request):
        e = request.app.state.engine
        async with e.lock:
            since = (datetime.fromisoformat(e.sample.timestamp) - timedelta(days=2)).isoformat()
            return forecast(e.storage.rows(e.run_id, since))

    @app.get("/api/export")
    async def export(request: Request):
        e = request.app.state.engine
        async with e.lock:
            rows = e.storage.rows(e.run_id)
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return Response("\ufeff" + stream.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="energia-experiment-{e.run_id}.csv"'})

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")
    return app


app = create_app()
