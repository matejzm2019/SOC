import asyncio
import csv
import io
import logging
import os
import secrets
import httpx
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .analytics import prediction, recommendations
from .assistant import AssistantService, facts_for
from .import_data import read_energy_csv, reprice_samples
from .models import AssistantApplyRequest, AssistantRequest, CHAT_SETTINGS, CsvImport, DemoCommand, Esp32Telemetry, SCENARIOS, Settings
from .prices import PriceService
from .simulator import Simulator
from .storage import Storage
from .weather import WeatherService

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
        self.weather = None
        self.prices = None
        self.chat_proposals = {}
        self.run_id = self.storage.latest_run()
        latest = self.storage.latest(self.run_id) if self.run_id else None
        if latest and latest.source == self.settings.measurement_source:
            self.sample = latest
            self.simulator = Simulator(self.settings, datetime.fromisoformat(latest.timestamp), latest.battery_energy_kwh)
            self.simulator.scenario = latest.scenario
        else:
            self.reset(self.settings)
        if self.settings.configured and not self.settings.demo_mode and self.settings.measurement_source == "hybrid":
            self.paused = False

    def reset(self, settings):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        if settings.demo_mode:
            end = now.replace(hour=10, minute=0, second=0)
            simulator = Simulator(settings, end - timedelta(days=1))
            samples = [simulator.step(seeded=True) for _ in range(288)]
        else:
            simulator = Simulator(settings, now - timedelta(seconds=1))
            samples = [simulator.step(seeded=True, interval_seconds=1)]
        samples = [self.price_sample(sample, settings) for sample in samples]
        run_id = self.storage.new_run(settings, samples if settings.demo_mode else [])
        self.settings, self.simulator, self.run_id = settings, simulator, run_id
        self.sample = samples[-1]
        self.paused = not (settings.configured and not settings.demo_mode and settings.measurement_source == "hybrid")
        self.error = None

    def configure(self, settings):
        if settings.measurement_source == "csv" and self.settings.measurement_source != "csv":
            raise HTTPException(422, "Pre importovanú históriu najprv nahrajte CSV v časti Zdroj dát.")
        if settings.measurement_source == "csv" and (settings.demo_mode or settings.battery_enabled or settings.wind_enabled):
            raise HTTPException(422, "Importovaná história nepodporuje demo režim ani modelovanie batérie a vetra. Pre plánovanie zmeňte zdroj údajov.")
        independent = {"ai_enabled", "ai_model", "weather_enabled", "location_name", "location_set", "weather_source"}
        physics_changed = any(getattr(settings, key) != getattr(self.settings, key) for key in Settings.model_fields if key not in independent)
        if physics_changed and settings.measurement_source != "csv":
            self.reset(settings)
        elif physics_changed and settings.measurement_source == "csv":
            samples = reprice_samples(self.storage.rows(self.run_id), settings)
            samples = [self.price_sample(sample, settings) for sample in samples]
            self.run_id = self.storage.new_run(settings, samples)
            self.sample = samples[-1]
            self.settings = self.simulator.settings = settings
        else:
            self.storage.save_settings(settings)
            self.settings = self.simulator.settings = settings

    def weather_state(self):
        return self.weather.view(self.settings) if self.weather else {"available": False, "stale": False, "source": self.settings.weather_source}

    def price_sample(self, sample, settings):
        if settings.price_source == "internet":
            rate = self.prices.quote(datetime.fromisoformat(sample.timestamp), sample.interval_seconds, settings) if self.prices and settings.prices_enabled else None
            return sample.model_copy(update={"buy_eur_kwh":rate,"price_source":"internet"})
        return sample.model_copy(update={"price_source":"manual"})

    def prediction(self):
        since = (datetime.fromisoformat(self.sample.timestamp) - timedelta(days=2, hours=1)).isoformat()
        return prediction(self.settings, self.weather_state(), self.storage.rows(self.run_id, since))

    def import_csv(self, content):
        samples = [self.price_sample(sample,self.settings) for sample in read_energy_csv(content, self.settings)]
        updated = self.settings.model_copy(update={"configured": True, "demo_mode": False,
                                                  "measurement_source": "csv", "battery_enabled": False, "wind_enabled": False,
                                                  "pv_enabled": any(sample.pv_w > 0 for sample in samples)})
        run_id = self.storage.new_run(updated, samples)
        self.settings, self.run_id, self.sample = updated, run_id, samples[-1]
        self.simulator = Simulator(updated, datetime.fromisoformat(self.sample.timestamp))
        self.paused, self.error = True, None
        return self.state()

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
            if not self.settings.demo_mode and self.settings.measurement_source == "hybrid":
                status = self.device_status()
                if not status["online"]:
                    raise RuntimeError("ESP32 neposlalo platné meranie za posledných 5 sekúnd")
                measured = self.device_telemetry
            interval = 300 if self.settings.demo_mode else 1
            if not self.settings.demo_mode:
                now = datetime.now(timezone.utc).replace(microsecond=0)
                elapsed = int((now - self.simulator.timestamp).total_seconds())
                if elapsed <= 0 and not self.sample.seeded:
                    return
                self.simulator.timestamp = now - timedelta(seconds=interval)
            sample = self.price_sample(self.simulator.step(measured=measured, interval_seconds=interval), self.settings)
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
                if not self.paused and self.settings.measurement_source != "csv":
                    try:
                        self.tick()
                    except RuntimeError as error:
                        self.error = str(error)
                        if self.settings.measurement_source != "hybrid":
                            self.paused = True
                    except Exception:
                        logger.exception("Simulátor bol pozastavený")
                        self.paused = True
                        self.error = "Chyba výpočtu alebo ukladania. Simulácia je pozastavená; skontrolujte log servera."

    def state(self):
        return {"settings": self.settings, "sample": self.sample, "device": self.device_status(), "weather": self.weather_state(),
                "prices": self.prices.view(self.settings) if self.prices else {"available":False,"source":"manual"},
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


def create_app(database=None, esp32_key=None, http_transport=None):
    @asynccontextmanager
    async def lifespan(app):
        engine = Engine(Path(database or os.environ.get("SOC_DATABASE", ROOT / "data" / "energy.sqlite3")),
                        esp32_key or device_key(ROOT / "data" / "device_key.txt"))
        async with httpx.AsyncClient(transport=http_transport, trust_env=False, limits=httpx.Limits(max_connections=8)) as client:
            engine.weather = WeatherService(client, engine.storage)
            engine.prices = PriceService(client, engine.storage)
            app.state.engine = engine
            app.state.assistant = AssistantService(client)
            tasks = [asyncio.create_task(engine.run())]
            if os.environ.get("SOC_OFFLINE") != "1":
                tasks.append(asyncio.create_task(engine.weather.run(engine)))
                tasks.append(asyncio.create_task(engine.prices.run(engine)))
            try:
                yield
            finally:
                for task in tasks:
                    task.cancel()
                for task in tasks:
                    with suppress(asyncio.CancelledError):
                        await task
                engine.storage.connection.close()

    app = FastAPI(title="Energia", version="0.7.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        if request.method in ("PUT", "POST", "DELETE", "PATCH"):
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                return Response("Cross-origin write rejected", status_code=403)
            if "application/json" not in request.headers.get("content-type", ""):
                return Response("JSON required", status_code=415)
            if len(await request.body()) > 3_100_000:
                return Response("Request too large", status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "geolocation=(self)"
        if request.url.path == "/":
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    async def health(request: Request):
        e = request.app.state.engine
        e.storage.connection.execute("SELECT 1").fetchone()
        return {"app": "energia", "status": "degraded" if e.error else "ok",
                "mode": "demo" if e.settings.demo_mode else "monitor", "version": app.version}

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
        await e.prices.refresh(value)
        async with e.lock:
            updated = value.model_copy(update={"configured": True})
            if updated != e.settings:
                e.configure(updated)
            return e.state()

    @app.get("/api/locations")
    async def locations(request: Request, q: str = Query(min_length=2, max_length=80)):
        try:
            return {"locations": await request.app.state.engine.weather.search(q)}
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise HTTPException(502, "Mestá sa nepodarilo vyhľadať. Skontrolujte internet alebo použite polohu.") from None

    @app.get("/api/weather")
    async def weather(request: Request):
        engine = request.app.state.engine
        await engine.weather.refresh(engine.settings)
        return engine.weather_state()

    @app.get("/api/assistant/status")
    async def assistant_status(request: Request, model: Literal["qwen3:0.6b", "qwen3:1.7b"] | None = None):
        settings = request.app.state.engine.settings
        if model:
            settings = settings.model_copy(update={"ai_model": model, "ai_enabled": True})
        return await request.app.state.assistant.status(settings, force=bool(model))

    @app.get("/api/prices")
    async def prices(request: Request):
        engine = request.app.state.engine
        await engine.prices.refresh(engine.settings)
        return engine.prices.view(engine.settings)

    @app.post("/api/assistant/chat")
    async def assistant_chat(value: AssistantRequest, request: Request):
        engine = request.app.state.engine
        async with engine.lock:
            settings_snapshot = engine.settings
            snapshot = engine.state()
            snapshot["settings"], snapshot["sample"] = engine.settings.model_dump(), engine.sample.model_dump()
            history = engine.storage.history(engine.run_id, "day")
            result = engine.prediction()
            facts = facts_for(snapshot, history, result)
        result = await request.app.state.assistant.chat(settings_snapshot, value.question, value.history, facts)
        changes = result.pop("changes", {})
        proposal = None
        if changes:
            try:
                values = settings_snapshot.model_dump() | changes
                if "demo_mode" in changes:
                    values["measurement_source"] = "simulator" if changes["demo_mode"] else "hybrid"
                if "buy_price" in changes:
                    values["price_source"] = changes.get("price_source", "manual")
                    values["price_mode"] = changes.get("price_mode", "manual")
                if "offpeak_price" in changes:
                    values["price_mode"] = changes.get("price_mode", "time_of_use")
                if any(key.startswith(("price_","buy_","sell_","offpeak_","distribution_","fixed_","supplier_","energy_vat")) for key in changes):
                    values["prices_enabled"] = changes.get("prices_enabled",True)
                updated = Settings.model_validate(values | {"configured":True})
                if updated.measurement_source == "csv" and (updated.battery_enabled or updated.wind_enabled):
                    raise ValueError("CSV nepodporuje batériu ani vietor. Najprv zmeň režim.")
                diff = {key:getattr(updated,key) for key in CHAT_SETTINGS if getattr(updated,key) != getattr(settings_snapshot,key)}
                if diff:
                    token = secrets.token_urlsafe(24)
                    async with engine.lock:
                        engine.chat_proposals = {k:p for k,p in engine.chat_proposals.items() if monotonic()-p["created"] < 600}
                        if len(engine.chat_proposals) >= 16:
                            engine.chat_proposals.pop(next(iter(engine.chat_proposals)))
                        engine.chat_proposals[token] = {"created":monotonic(), "before":settings_snapshot, "after":updated,
                                                       "run_id":snapshot["demo"]["run_id"]}
                    proposal = {"token":token, "changes":[{"label":CHAT_SETTINGS[key],"before":getattr(settings_snapshot,key),"after":after} for key,after in diff.items()]}
                    result["answer"] = "Pripravil som návrh nastavení. Skontroluj zmeny a stlač Použiť zmenu; zatiaľ sa nič nezmenilo."
                    result["numeric_guard_passed"] = True
                else:
                    result["answer"] = "Tieto nastavenia už majú požadované hodnoty. Nič netreba meniť."
            except (ValidationError,ValueError):
                result["answer"] = "Návrh nie je platný pre aktuálny režim alebo povolený rozsah. Nič sa nezmenilo; upresni hodnotu a jednotku."
        return {**result, "proposal":proposal, "run_id": snapshot["demo"]["run_id"]}

    @app.post("/api/assistant/apply")
    async def assistant_apply(value: AssistantApplyRequest, request: Request):
        engine = request.app.state.engine
        async with engine.lock:
            proposal = engine.chat_proposals.get(value.token)
            if not proposal or monotonic()-proposal["created"] >= 600:
                raise HTTPException(410,"Návrh vypršal alebo už bol použitý. Požiadaj asistenta o nový návrh.")
            if engine.settings != proposal["before"] or engine.run_id != proposal["run_id"]:
                raise HTTPException(409,"Nastavenia sa medzitým zmenili. Požiadaj o nový návrh.")
        await engine.prices.refresh(proposal["after"])
        async with engine.lock:
            if value.token not in engine.chat_proposals or engine.settings != proposal["before"] or engine.run_id != proposal["run_id"]:
                raise HTTPException(409,"Návrh už nie je aktuálny. Požiadaj o nový návrh.")
            engine.configure(proposal["after"])
            del engine.chat_proposals[value.token]
            return engine.state()

    @app.post("/api/import")
    async def import_csv(value: CsvImport, request: Request):
        engine = request.app.state.engine
        async with engine.lock:
            try:
                return engine.import_csv(value.content)
            except (ValueError, csv.Error) as error:
                raise HTTPException(422, str(error)) from None

    @app.get("/api/runs")
    async def runs(request: Request):
        return {"runs": request.app.state.engine.storage.runs()}

    @app.get("/api/import/template")
    async def import_template():
        text = "timestamp,interval_minutes,load_kwh,pv_kwh\n2026-09-01T01:00:00+02:00,60,0.35,0\n2026-09-01T02:00:00+02:00,60,0.28,0\n"
        return Response("\ufeff" + text, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="energia-import-template.csv"'})

    @app.post("/api/demo")
    async def demo(command: DemoCommand, request: Request):
        e = request.app.state.engine
        async with e.lock:
            if e.settings.measurement_source == "csv":
                raise HTTPException(409, "Importovaná história sa neprehráva. Pre simuláciu zmeňte zdroj údajov.")
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
    async def history(request: Request, period: Literal["day", "week", "month", "all"] = "day", run_id: int | None = Query(default=None, ge=1)):
        e = request.app.state.engine
        async with e.lock:
            selected = run_id or e.run_id
            if not e.storage.run_exists(selected):
                raise HTTPException(404, "História neexistuje.")
            return e.storage.history(selected, period)

    @app.get("/api/forecast")
    async def prediction(request: Request):
        e = request.app.state.engine
        async with e.lock:
            return e.prediction()

    @app.get("/api/export")
    async def export(request: Request, run_id: int | None = Query(default=None, ge=1)):
        e = request.app.state.engine
        async with e.lock:
            selected = run_id or e.run_id
            rows = e.storage.rows(selected)
        if not rows:
            raise HTTPException(404, "História neexistuje.")
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(key for row in rows for key in row)))
        writer.writeheader()
        writer.writerows(rows)
        return Response("\ufeff" + stream.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="energia-experiment-{selected}.csv"'})

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")
    return app


app = create_app()
