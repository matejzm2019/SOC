from datetime import datetime, timedelta, timezone
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.assistant import grounded_answer
from backend.main import create_app
from backend.models import Esp32Telemetry, Settings
from backend.prices import PriceService
from backend.simulator import Simulator
from backend.storage import Storage


def test_chat_keeps_text_lists_device_names_and_verified_unit_conversions():
    facts = [{"id":"F1", "value":"2.40 kW"}, {"id":"F2", "value":"65.0 %"}]
    text = "1. ESP32 posiela údaje. Spotreba je 2,4 kW (2400 W). Nabitie je [F2]."
    answer, valid = grounded_answer(text, facts)
    assert valid and "ESP32" in answer and "1." in answer and "2400 W" in answer and "65.0 %" in answer
    answer, valid = grounded_answer("ESP32 je pripojené. Spotreba je 999 kW. Sledujte graf.", facts)
    assert not valid and "999" not in answer and "ESP32 je pripojené." in answer and "Sledujte graf." in answer
    assert "údaj nie je dostupný" in grounded_answer("Hodnota [F99]. Ostatné údaje fungujú.", facts)[0]


def test_spot_interval_conversion_tax_negative_prices_and_missing_coverage(tmp_path):
    storage = Storage(tmp_path / "prices.sqlite3")
    service = PriceService(None, storage)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now - timedelta(minutes=30)
    payload = {"unit":"EUR / MWh", "unix_seconds":[start.timestamp(), (start+timedelta(minutes=15)).timestamp()], "price":[100,-20]}
    service.points = service.parse(payload)
    service.snapshot = {"data":payload, "fetched_at":now.isoformat()}
    settings = Settings(price_source="internet", supplier_markup=.01, energy_vat_pct=20)
    assert service.quote(now,1800,settings) == pytest.approx(.06)
    assert service.quote(now,900,settings) == pytest.approx(-.012)
    assert service.quote(now+timedelta(minutes=1),1800,settings) is None
    for invalid in (payload | {"unit":"EUR/kWh"}, payload | {"price":[float('nan'),100]}, payload | {"unix_seconds":[1,1]}):
        with pytest.raises(ValueError):
            service.parse(invalid)
    service.snapshot["fetched_at"] = (now-timedelta(hours=37)).isoformat()
    assert service.quote(now,900,settings) is None
    storage.connection.close()


def test_internet_price_selection_cache_outage_and_no_historical_price_fabrication(tmp_path, monkeypatch):
    monkeypatch.setenv("SOC_OFFLINE", "1")
    calls, fail = [], [False]
    start = datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=1)
    payload = {"unit":"EUR / MWh", "unix_seconds":[(start+timedelta(minutes=15*i)).timestamp() for i in range(288)], "price":[120]*288}
    def respond(request):
        calls.append(request)
        assert request.url.host == "api.energy-charts.info" and request.url.params["bzn"] == "SK"
        if fail[0]:
            raise httpx.ReadTimeout("offline",request=request)
        return httpx.Response(200,json=payload)
    app = create_app(tmp_path / "db.sqlite3", "secret", httpx.MockTransport(respond))
    with TestClient(app) as client:
        settings = client.get('/api/state').json()['settings'] | {"price_source":"internet","supplier_markup":.02,"energy_vat_pct":10}
        saved = client.put('/api/settings',json=settings).json()
        assert saved['prices']['buy_eur_kwh'] == pytest.approx(.154)
        assert saved['sample']['buy_eur_kwh'] == pytest.approx(.154)
        assert client.get('/api/prices').json()['available'] and len(calls) == 1
        service = app.state.engine.prices
        service.snapshot['fetched_at'] = (datetime.now(timezone.utc)-timedelta(hours=2)).isoformat()
        service.attempted_at -= 61
        fail[0] = True
        cached = client.get('/api/prices').json()
        assert cached['available'] and cached['stale'] and cached['error']
        csv = 'timestamp,interval_minutes,load_kwh\n2020-01-01T01:00:00Z,60,1\n'
        imported = client.post('/api/import',json={'content':csv}).json()
        assert imported['sample']['buy_eur_kwh'] is None
        assert client.get('/api/history').json()['totals']['cost_eur'] is None
        manual = client.put('/api/settings',json=imported['settings'] | {'price_source':'manual','price_mode':'manual','buy_price':.25}).json()
        assert manual['sample']['buy_eur_kwh'] == .25


def test_cell_telemetry_is_real_soc_and_separate_from_house_supply(tmp_path, monkeypatch):
    monkeypatch.setenv('SOC_OFFLINE','1')
    data = {'panel_voltage_v':6,'panel_current_a':.02,'panel_power_w':.12,
            'battery_voltage_v':3.95,'battery_soc_pct':65,'battery_charge_rate_pct_h':2.5}
    settings = Settings(demo_mode=False,battery_capacity_mah=2000)
    sample = Simulator(settings,datetime.now(timezone.utc)).step(measured=Esp32Telemetry(**data),interval_seconds=1)
    assert sample.soc_pct == 65 and sample.battery_voltage_v == 3.95
    assert sample.battery_energy_kwh * 1000 == pytest.approx(4.81)
    assert sample.battery_w == 0 and sample.battery_eta_hours is None
    assert sample.pv_w + sample.grid_w == pytest.approx(sample.served_w)
    with TestClient(create_app(tmp_path / 'db.sqlite3','secret')) as client:
        initial = client.get('/api/state').json()
        client.put('/api/settings',json=initial['settings'] | {'demo_mode':False,'battery_capacity_mah':2000}).raise_for_status()
        client.post('/api/device/telemetry',json=data,headers={'X-Device-Key':'secret'}).raise_for_status()
        client.portal.call(client.app.state.engine.tick)
        assert client.get('/api/state').json()['sample']['soc_pct'] == 65
        assert client.get('/api/history').json()['points'][0]['soc_pct'] == 65
        assert 'battery_voltage_v' in client.get('/api/export').text
        # Old firmware remains compatible but never invents a physical SOC.
        old = {k:v for k,v in data.items() if not k.startswith('battery_')}
        legacy = Simulator(settings,datetime.now(timezone.utc)).step(measured=Esp32Telemetry(**old),interval_seconds=1)
        assert legacy.soc_pct is None and legacy.battery_energy_kwh is None
        for bad in (old | {'battery_voltage_v':3.9}, data | {'battery_soc_pct':101}, data | {'battery_voltage_v':5}):
            assert client.post('/api/device/telemetry',json=bad,headers={'X-Device-Key':'secret'}).status_code == 422


def test_export_keeps_old_samples_when_new_optional_fields_appear(tmp_path, monkeypatch):
    monkeypatch.setenv('SOC_OFFLINE','1')
    with TestClient(create_app(tmp_path / 'db.sqlite3','secret')) as client:
        storage = client.app.state.engine.storage
        def make_legacy_row():
            row = storage.connection.execute('SELECT id,payload FROM samples ORDER BY id LIMIT 1').fetchone()
            old = json.loads(row[1])
            for field in ('battery_voltage_v','battery_charge_rate_pct_h','price_source'):
                old.pop(field)
            with storage.connection:
                storage.connection.execute('UPDATE samples SET payload=? WHERE id=?',(json.dumps(old),row[0]))
        client.portal.call(make_legacy_row)
        exported = client.get('/api/export')
        assert exported.status_code == 200 and 'battery_voltage_v' in exported.text
