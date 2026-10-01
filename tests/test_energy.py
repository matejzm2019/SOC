from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.analytics import forecast
from backend.main import Engine, create_app
from backend.models import SCENARIOS, Esp32Telemetry, Settings
from backend.simulator import EFFICIENCY, Simulator, turbine_power
from backend.storage import Storage

START = datetime(2026, 6, 21, 10, tzinfo=timezone.utc)


@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("battery", [True, False])
def test_balance_and_battery_limits(scenario, battery):
    settings = Settings(battery_enabled=battery, wind_enabled=True, battery_kwh=1, battery_max_kw=10)
    sim = Simulator(settings, START)
    sim.set_scenario(scenario)
    for _ in range(300):
        before = sim.energy
        s = sim.step()
        assert s.pv_w + s.wind_w + s.grid_w + s.battery_w == pytest.approx(s.served_w + s.curtailed_w, abs=1e-7)
        assert s.load_w == pytest.approx(s.served_w + s.unserved_w)
        if battery:
            assert 10 - 1e-8 <= s.soc_pct <= 100 + 1e-8
            assert abs(s.battery_w) <= settings.battery_max_kw * 1000 + 1e-8
            factor = 1 / EFFICIENCY if s.battery_w >= 0 else EFFICIENCY
            assert sim.energy == pytest.approx(before - s.battery_w * s.interval_seconds / 3600000 * factor)
        else:
            assert s.battery_w == 0 and s.soc_pct is None
        if scenario == "outage":
            assert s.grid_w == 0 and not s.grid_available


def test_outage_without_sources():
    sim = Simulator(Settings(pv_enabled=False, wind_enabled=False, battery_enabled=False), START)
    sim.set_scenario("outage")
    s = sim.step()
    assert s.served_w == 0 and s.voltage_v == 0 and s.current_a == 0
    assert s.unserved_w == s.load_w


def test_no_sources_import_equals_load():
    sim = Simulator(Settings(pv_enabled=False, wind_enabled=False, battery_enabled=False), START)
    s = sim.step()
    assert s.grid_w == s.load_w


@pytest.mark.parametrize("wind,expected", [(0,0),(3,0),(5,80),(8,350),(12,1000),(24,1000),(25,0),(30,0)])
def test_turbine_curve(wind, expected):
    assert turbine_power(wind, 1000) == pytest.approx(expected)


def test_integration_and_economy(tmp_path):
    settings = Settings(pv_enabled=False, wind_enabled=False, battery_enabled=False)
    sim = Simulator(settings, START)
    rows = [sim.step() for _ in range(12)]
    db = Storage(tmp_path / "db.sqlite3")
    run = db.new_run(settings)
    db.save(run, rows)
    history = db.history(run, "all")
    t = history["totals"]
    expected = sum(s.load_w for s in rows) / 12000
    assert t["load_kwh"] == pytest.approx(expected)
    assert t["import_kwh"] == pytest.approx(expected)
    assert t["cost_eur"] == pytest.approx(expected * .24 + .25 / 24)
    assert t["savings_eur"] == pytest.approx(0)
    assert history["duration_hours"] == 1
    db.connection.close()


def test_export_economy_and_disabled_prices(tmp_path):
    settings = Settings(battery_enabled=False)
    sim = Simulator(settings, START)
    sim.set_scenario("surplus")
    s = sim.step()
    assert s.grid_w < 0
    db = Storage(tmp_path / "db.sqlite3")
    run = db.new_run(settings)
    db.save(run, [s])
    totals = db.history(run, "day")["totals"]
    exported = -s.grid_w / 12000
    assert totals["export_revenue_eur"] == pytest.approx(exported * .06)
    assert totals["cost_eur"] == pytest.approx(-exported * .06 + .25 / 288)
    disabled = settings.model_copy(update={"prices_enabled": False})
    run = db.new_run(disabled)
    db.save(run, [Simulator(disabled, START).step()])
    assert db.history(run, "all")["totals"]["cost_eur"] is None
    db.connection.close()


def test_time_tariff_and_scenario_override():
    settings = Settings(price_mode="time_of_use")
    # Bratislava 01:00 in summer.
    sim = Simulator(settings, datetime(2026,6,20,23,tzinfo=timezone.utc))
    assert sim.step().buy_eur_kwh == settings.offpeak_price
    sim = Simulator(settings, START)
    assert sim.step().buy_eur_kwh == settings.buy_price
    sim.set_scenario("cheap")
    assert sim.step().buy_eur_kwh == .03
    sim.set_scenario("expensive")
    assert sim.step().buy_eur_kwh == .55


def test_hybrid_measurement_scales_panel_and_load():
    settings = Settings(measurement_source="hybrid", pv_kwp=6, pv_reference_w=.5,
                        battery_enabled=False, base_load_w=600)
    measured = Esp32Telemetry(panel_voltage_v=5, panel_current_a=.05, panel_power_w=.25,
                              illuminance_lux=42000, temperature_c=31, load_stage=2)
    sample = Simulator(settings, START).step(measured=measured)
    assert sample.pv_w == pytest.approx(3000)
    assert sample.source == "hybrid" and sample.quality == "mixed"
    assert sample.panel_power_w == .25 and sample.illuminance_lux == 42000
    assert sample.temperature_c == 31 and sample.load_w >= 1100
    assert sample.pv_w + sample.grid_w == pytest.approx(sample.served_w)


def test_monitor_interval_uses_real_elapsed_time():
    sim = Simulator(Settings(demo_mode=False, battery_enabled=False), START)
    sample = sim.step(interval_seconds=1)
    assert sample.interval_seconds == 1
    assert sim.timestamp.timestamp() - START.timestamp() == 1


def test_forecast_baseline_and_holdout():
    rows = []
    sim = Simulator(Settings(), START)
    for _ in range(576):
        rows.append(sim.step().model_dump())
    assert not forecast(rows[:287])["available"]
    first = forecast(rows[:288])
    assert len(first["points"]) == 24 and first["metrics"] is None
    prediction = forecast(rows)
    assert datetime.fromisoformat(prediction["points"][0]["timestamp"]) > sim.timestamp
    assert prediction["points"][0]["load_w"] == pytest.approx(sum(r["load_w"] for r in rows[288:300]) / 12)
    expected = sum(abs(rows[i]["load_w"] - rows[i-288]["load_w"]) for i in range(288,576)) / 288
    assert prediction["metrics"]["load_w"]["mae_w"] == pytest.approx(expected)


def test_failed_write_does_not_advance_simulation(tmp_path, monkeypatch):
    engine = Engine(tmp_path / "db.sqlite3")
    timestamp, energy, previous = engine.simulator.timestamp, engine.simulator.energy, engine.sample
    def fail(*args):
        raise OSError("disk full")
    monkeypatch.setattr(engine.storage, "save", fail)
    with pytest.raises(OSError):
        engine.tick()
    assert engine.simulator.timestamp == timestamp
    assert engine.simulator.energy == energy
    assert engine.sample == previous
    engine.storage.connection.close()


def test_api_lifecycle_validation_restart_and_export(tmp_path):
    path = tmp_path / "energy.sqlite3"
    with TestClient(create_app(path, "test-secret")) as client:
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/api/health").json()["status"] == "ok"
        initial = client.get("/api/state").json()
        assert initial["demo"]["paused"]
        assert client.get("/api/history").json()["sample_count"] == 288
        assert client.put("/api/settings", json={"battery_kwh":-1}).status_code == 422
        assert client.put("/api/settings", json={"measurement_source":"mqtt"}).status_code == 422
        assert client.post("/api/demo", json={"scenario":"unknown"}).status_code == 422
        assert client.post("/api/demo", json={"speed":300}).status_code == 422
        assert client.post("/api/demo", json={"step":True,"paused":False}).status_code == 422
        assert client.post("/api/demo", json={"paused":True}, headers={"Origin":"https://evil.example"}).status_code == 403
        assert client.get("/api/state", headers={"Host":"192.168.1.50:8765"}).status_code == 200
        assert client.get("/api/history?period=bad").status_code == 422
        settings = initial["settings"] | {"prices_enabled":False,"pv_enabled":False,"battery_enabled":False}
        saved = client.put("/api/settings", json=settings).json()
        assert saved["settings"]["configured"] and saved["demo"]["run_id"] != initial["demo"]["run_id"]
        unchanged = client.put("/api/settings", json=saved["settings"]).json()
        assert unchanged["demo"]["run_id"] == saved["demo"]["run_id"]
        assert client.get("/api/history").json()["totals"]["cost_eur"] is None
        outage = client.post("/api/demo", json={"scenario":"outage"}).json()
        assert outage["sample"]["grid_w"] == 0 and outage["sample"]["unserved_w"] > 0
        timestamp = outage["sample"]["timestamp"]
        assert client.get("/api/forecast").json()["available"]
        exported = client.get("/api/export")
        assert "text/csv" in exported.headers["content-type"]
        assert "synthetic" in exported.text and "unserved_w" in exported.text
        assert client.get("/api/history?period=all").json()["sample_count"] == 289
    with TestClient(create_app(path, "test-secret")) as client:
        restored = client.get("/api/state").json()
        assert restored["sample"]["timestamp"] == timestamp
        assert not restored["settings"]["prices_enabled"]
        assert restored["demo"]["scenario"] == "outage"
        assert restored["demo"]["paused"]


def test_esp32_auth_status_and_hybrid_step(tmp_path):
    path = tmp_path / "energy.sqlite3"
    telemetry = {"device_id":"soc-panel", "firmware_version":"0.1.0",
                 "panel_voltage_v":5.1, "panel_current_a":.1, "panel_power_w":.5,
                 "illuminance_lux":50000, "temperature_c":27, "load_stage":1,
                 "grid_available":True}
    with TestClient(create_app(path, "test-secret")) as client:
        assert client.post("/api/device/telemetry", json=telemetry).status_code == 401
        accepted = client.post("/api/device/telemetry", json=telemetry,
                               headers={"X-Device-Key":"test-secret"})
        assert accepted.status_code == 200 and accepted.json()["accepted"]
        state = client.get("/api/state").json()
        assert state["device"]["online"] and state["device"]["telemetry"]["device_id"] == "soc-panel"
        settings = state["settings"] | {"measurement_source":"hybrid", "pv_reference_w":.5}
        hybrid = client.put("/api/settings", json=settings).json()
        assert hybrid["settings"]["measurement_source"] == "hybrid"
        stepped = client.post("/api/demo", json={"step":True}).json()
        assert stepped["sample"]["source"] == "hybrid"
        assert stepped["sample"]["device_id"] == "soc-panel"


def test_hybrid_step_requires_recent_device_data(tmp_path):
    with TestClient(create_app(tmp_path / "energy.sqlite3", "test-secret")) as client:
        settings = client.get("/api/state").json()["settings"] | {"measurement_source":"hybrid"}
        client.put("/api/settings", json=settings)
        response = client.post("/api/demo", json={"step":True})
        assert response.status_code == 409
        assert "ESP32" in response.json()["detail"]


def test_monitor_mode_disables_demo_controls(tmp_path):
    with TestClient(create_app(tmp_path / "energy.sqlite3", "test-secret")) as client:
        settings = client.get("/api/state").json()["settings"] | {"demo_mode":False}
        state = client.put("/api/settings", json=settings).json()
        assert not state["demo"]["enabled"]
        assert state["demo"]["step_seconds"] == 1
        assert state["sample"]["interval_seconds"] == 1
        assert client.get("/api/history?period=all").json()["sample_count"] == 1
        assert client.get("/api/health").json()["mode"] == "monitor"
        for payload in ({"scenario":"cloudy"}, {"speed":5}, {"step":True}):
            response = client.post("/api/demo", json=payload)
            assert response.status_code == 409
            assert "DEMO MODE" in response.json()["detail"]
        assert client.post("/api/demo", json={"paused":False}).status_code == 200
