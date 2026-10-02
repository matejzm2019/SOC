from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.analytics import forecast
from backend.assistant import grounded_answer, ollama_url
from backend.main import create_app
from backend.import_data import read_energy_csv
from backend.models import Settings
from backend.simulator import Simulator


@pytest.fixture(autouse=True)
def offline_background(monkeypatch):
    monkeypatch.setenv("SOC_OFFLINE", "1")


def weather_payload():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now.replace(hour=0, minute=0, second=0)
    values = {"temperature_2m": 20, "cloud_cover": 30, "wind_speed_10m": 4,
              "shortwave_radiation": 500, "global_tilted_irradiance": 600,
              "precipitation": 0.1, "weather_code": 2}
    return {"current": {"time": now.timestamp(), **values},
            "hourly": {"time": [(start + timedelta(hours=i)).timestamp() for i in range(72)],
                       **{key: [value] * 72 for key, value in values.items()}}}


def transport_fixture(calls, failures=None, answer="Spotreba v poslednom intervale je [F3]."):
    def respond(request):
        calls.append(request)
        if failures and failures[0]:
            raise httpx.ReadTimeout("offline", request=request)
        if request.url.host == "geocoding-api.open-meteo.com":
            return httpx.Response(200, json={"results": [{"name": "Žilina", "admin1": "Žilinský kraj", "country": "Slovensko", "latitude": 49.22312, "longitude": 18.73941}]})
        if request.url.host == "api.open-meteo.com":
            assert request.url.params["wind_speed_unit"] == "ms"
            assert request.url.params["azimuth"] == "0.0"
            return httpx.Response(200, json=weather_payload())
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:0.6b"}]})
        if request.url.path == "/api/chat":
            return httpx.Response(200, json={"message": {"content": answer}, "done_reason": "stop"})
        return httpx.Response(404)
    return httpx.MockTransport(respond)


def set_location(client, **changes):
    settings = client.get("/api/state").json()["settings"] | {
        "location_name": "Žilina, Slovensko", "location_set": True, "latitude": 49.223, "longitude": 18.739,
        "weather_source": "internet", **changes}
    response = client.put("/api/settings", json=settings)
    assert response.status_code == 200, response.text
    return response.json()


def test_city_weather_cache_and_persisted_outage(tmp_path):
    calls, failures, path = [], [False], tmp_path / "db.sqlite3"
    app = create_app(path, "secret", transport_fixture(calls, failures))
    with TestClient(app) as client:
        assert client.get("/api/weather").json()["available"] is False
        location = client.get("/api/locations?q=Žilina").json()["locations"][0]
        assert location["latitude"] == 49.223
        client.get("/api/locations?q=Žilina")
        assert len(calls) == 1
        set_location(client)
        weather = client.get("/api/weather").json()
        assert weather["available"] and not weather["stale"]
        assert weather["current"]["wind_ms"] == 4 and weather["current"]["radiation_wm2"] == 500
        assert len(weather["hourly"]) == 72
        client.get("/api/weather")
        assert len(calls) == 2
        cache = app.state.engine.weather.snapshot
        cache["fetched_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        client.portal.call(app.state.engine.storage.cache_put, "weather", cache)
        failures[0] = True
        old = client.get("/api/weather").json()
        assert old["stale"] and old["available"] and old["error"]
        assert old["current"] == weather["current"]
    with TestClient(create_app(path, "secret", transport_fixture([], failures))) as client:
        persisted = client.get("/api/state").json()["weather"]
        assert persisted["available"] and persisted["stale"]


def test_planning_real_weather_no_fabricated_seed_and_forecast(tmp_path):
    calls = []
    app = create_app(tmp_path / "db.sqlite3", "secret", transport_fixture(calls))
    with TestClient(app) as client:
        bad = client.get("/api/state").json()["settings"] | {"measurement_source": "planning", "demo_mode": False}
        assert client.put("/api/settings", json=bad).status_code == 422
        state = set_location(client, measurement_source="planning", demo_mode=False)
        assert not state["demo"]["paused"]
        assert client.get("/api/history").json()["sample_count"] == 0
        client.get("/api/weather")
        state = client.get("/api/state").json()
        assert state["sample"]["source"] == "planning" and state["sample"]["quality"] == "estimated"
        assert state["sample"]["temperature_c"] == 20
        assert state["sample"]["pv_w"] == pytest.approx(6 * 600 * .86)
        assert client.get("/api/history").json()["sample_count"] == 1
        result = client.get("/api/forecast").json()
        assert result["weather_based"] and result["load_assumed"] and len(result["points"]) == 24
        assert result["points"][0]["pv_w"] == pytest.approx(6 * 600 * .86)
        app.state.engine.weather.snapshot["fetched_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        previous = app.state.engine.sample
        with pytest.raises(RuntimeError):
            app.state.engine.tick()
        assert app.state.engine.sample == previous


def test_csv_atomic_import_archive_tariff_and_missing_measurements(tmp_path):
    csv = "timestamp,interval_minutes,load_kwh,pv_kwh\n2026-09-01T01:00:00+02:00,60,1,0.3\n2026-09-01T02:00:00+02:00,60,0.5,0\n"
    with TestClient(create_app(tmp_path / "db.sqlite3", "secret", transport_fixture([]))) as client:
        old_run = client.get("/api/state").json()["demo"]["run_id"]
        response = client.post("/api/import", json={"content": csv})
        assert response.status_code == 200, response.text
        state = response.json()
        assert state["sample"]["source"] == "csv" and state["sample"]["voltage_v"] is None
        assert not state["settings"]["battery_enabled"] and not state["settings"]["demo_mode"]
        assert client.post("/api/demo", json={"paused": False}).status_code == 409
        history = client.get("/api/history?period=all").json()
        assert history["totals"]["load_kwh"] == 1.5 and history["totals"]["import_kwh"] == pytest.approx(1.2)
        assert client.get(f"/api/history?run_id={old_run}").json()["sample_count"] == 288
        assert len(client.get("/api/runs").json()["runs"]) == 2
        state_run = state["demo"]["run_id"]
        invalid = csv.replace("0.5,0", "NaN,0")
        assert client.post("/api/import", json={"content": invalid}).status_code == 422
        assert client.get("/api/state").json()["demo"]["run_id"] == state_run
        saved = client.put("/api/settings", json=state["settings"] | {"buy_price": .3}).json()
        assert saved["demo"]["run_id"] != state_run and saved["sample"]["quality"] == "imported"
        assert client.get("/api/history?period=all").json()["totals"]["load_kwh"] == 1.5
        assert client.get("/api/history?period=all").json()["totals"]["cost_eur"] > history["totals"]["cost_eur"]
        assert client.get("/api/history?run_id=99999").status_code == 404
        assert client.get("/api/import/template").status_code == 200


@pytest.mark.parametrize("bad", [
    "2026-09-01T01:00:00,60,1", "2026-09-01T01:00:00Z,0,1",
    "2026-09-01T01:00:00Z,60,-1", "2026-09-01T01:00:00Z,60,inf",
    "2026-09-01T01:00:00Z,60,1\n2026-09-01T01:30:00Z,60,2",
])
def test_invalid_csv_is_rejected(tmp_path, bad):
    with TestClient(create_app(tmp_path / "db.sqlite3", "secret", transport_fixture([]))) as client:
        assert client.post("/api/import", json={"content": "timestamp,interval_minutes,load_kwh\n" + bad}).status_code == 422


@pytest.mark.parametrize("content", [
    "\ufeff" * 10,
    "timestamp,interval_minutes,load_kwh\n2026-09-01T01:00:00Z\n",
    "timestamp,interval_minutes,load_kwh\n0001-01-01T00:00:00Z,60,1\n",
    "timestamp,interval_minutes,load_kwh\n" + "9" * 140000 + ",60,1\n",
], ids=["empty", "missing-fields", "time-overflow", "oversized-field"])
def test_malformed_csv_keeps_previous_data(tmp_path, content):
    with TestClient(create_app(tmp_path / "db.sqlite3", "secret", transport_fixture([]))) as client:
        run = client.get("/api/state").json()["demo"]["run_id"]
        assert client.post("/api/import", json={"content": content}).status_code == 422
        assert client.get("/api/state").json()["demo"]["run_id"] == run


def test_forecast_requires_duration_not_sample_count():
    sim = Simulator(Settings(demo_mode=False), datetime(2026, 9, 1, tzinfo=timezone.utc))
    rows = [sim.step(interval_seconds=1).model_dump() for _ in range(288)]
    assert not forecast(rows)["available"]
    sim = Simulator(Settings(), datetime(2026, 9, 1, tzinfo=timezone.utc))
    full_day = [sim.step().model_dump() for _ in range(288)]
    assert forecast(full_day)["available"]
    assert not forecast(full_day[:100] + full_day[101:])["available"]


def test_assistant_local_grounded_prompt_and_settings_keep_history(tmp_path):
    calls = []
    with TestClient(create_app(tmp_path / "db.sqlite3", "secret", transport_fixture(calls))) as client:
        state = client.get("/api/state").json()
        status = client.get("/api/assistant/status").json()
        assert status["available"] and status["local_only"]
        result = client.post("/api/assistant/chat", json={"question": "Aká je spotreba?"})
        assert result.status_code == 200, result.text
        data = result.json()
        assert data["numeric_guard_passed"] and "[F3]" not in data["answer"]
        assert data["facts"][2]["value"] in data["answer"]
        import json
        request = next(r for r in calls if r.url.path == "/api/chat")
        body = json.loads(request.content)
        assert body["think"] is False and body["options"]["num_ctx"] == 2048
        assert request.url.host == "127.0.0.1"
        saved = client.put("/api/settings", json=state["settings"] | {"ai_enabled": False}).json()
        # configured=True creates the initial run; subsequent assistant changes preserve it.
        again = client.put("/api/settings", json=saved["settings"] | {"ai_enabled": True}).json()
        assert again["demo"]["run_id"] == saved["demo"]["run_id"]
        assert client.get("/api/assistant/status?model=unsafe:cloud").status_code == 422


def test_assistant_unverified_numbers_missing_model_and_timeout(tmp_path):
    facts = [{"id": "F1", "value": "2.4 kW"}]
    assert grounded_answer("Výkon je [F1].", facts) == ("Výkon je 2.4 kW.", True)
    assert not grounded_answer("Výkon je 999 kW.", facts)[1]
    assert not grounded_answer("Výkon je [F99].", facts)[1]
    with TestClient(create_app(tmp_path / "bad.sqlite3", "secret", transport_fixture([], answer="Výkon je 999 kW."))) as client:
        result = client.post("/api/assistant/chat", json={"question": "Zhrň výkon"}).json()
        assert not result["numeric_guard_passed"] and "999" not in result["answer"]
    def missing(request):
        return httpx.Response(200, json={"models": []})
    with TestClient(create_app(tmp_path / "missing.sqlite3", "secret", httpx.MockTransport(missing))) as client:
        assert not client.get("/api/assistant/status").json()["available"]
        assert client.post("/api/assistant/chat", json={"question": "Zhrň"}).status_code == 503
    def timeout(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:0.6b"}]})
        raise httpx.ReadTimeout("slow", request=request)
    with TestClient(create_app(tmp_path / "timeout.sqlite3", "secret", httpx.MockTransport(timeout))) as client:
        assert client.post("/api/assistant/chat", json={"question": "Zhrň"}).status_code == 504


def test_ollama_endpoint_cannot_be_remote(monkeypatch):
    monkeypatch.setenv("SOC_OLLAMA_URL", "https://example.com")
    with pytest.raises(ValueError):
        ollama_url()


def test_csv_tariff_uses_interval_not_ending_hour():
    rows = read_energy_csv("timestamp,interval_minutes,load_kwh\n2026-09-01T22:00:00+02:00,60,1\n2026-09-01T23:00:00+02:00,60,1\n",
                           Settings(price_mode="time_of_use", buy_price=.2, offpeak_price=.1))
    assert rows[0].buy_eur_kwh == .2 and rows[1].buy_eur_kwh == .1
    crossing = read_energy_csv("timestamp,interval_minutes,load_kwh\n2026-09-01T22:30:00+02:00,60,1\n",
                              Settings(price_mode="time_of_use", buy_price=.2, offpeak_price=.1))
    assert crossing[0].buy_eur_kwh == pytest.approx(.15)


def test_history_clips_interval_at_rolling_day_boundary(tmp_path):
    content = "timestamp,interval_minutes,load_kwh\n2026-09-01T12:00:00Z,1440,24\n2026-09-02T00:00:00Z,720,12\n"
    with TestClient(create_app(tmp_path / "db.sqlite3", "secret", transport_fixture([]))) as client:
        assert client.post("/api/import", json={"content": content}).status_code == 200
        day = client.get("/api/history?period=day").json()
        assert day["duration_hours"] == 24 and day["totals"]["load_kwh"] == 24
        assert client.get("/api/history?period=all").json()["totals"]["load_kwh"] == 36


def test_malformed_weather_never_replaces_valid_cache(tmp_path):
    broken = [False]
    def response(request):
        payload = weather_payload()
        if broken[0]:
            payload["current"]["temperature_2m"] = None
        return httpx.Response(200, json=payload)
    app = create_app(tmp_path / "db.sqlite3", "secret", httpx.MockTransport(response))
    with TestClient(app) as client:
        set_location(client)
        original = client.get("/api/weather").json()["current"]
        app.state.engine.weather.snapshot["fetched_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        broken[0] = True
        weather = client.get("/api/weather").json()
        assert weather["current"] == original and weather["stale"] and weather["error"]
