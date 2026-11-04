import csv
import io
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime,timezone
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.models import Esp32Telemetry,Settings
from backend.simulator import Simulator
from backend.water import WaterAction,WaterConfig,WaterController
from backend.storage import Storage

ROOT=Path(__file__).resolve().parents[1]
BASE=dict(panel_voltage_v=6,panel_current_a=.03,panel_power_w=.18,
          grid_available=True,load_stage=3,battery_voltage_v=3.8,battery_soc_pct=50,
          battery_current_a=-.2,battery_soc_method='voltage_estimate',telemetry_origin='software_test')
WATER=dict(source_ok=True,target_low=True,target_full=False,leak_detected=False,pump_running=False,fault='none')


def test_house_telemetry_is_labelled_and_not_a_kw_battery():
 t=Esp32Telemetry(**BASE)
 s=Simulator(Settings(demo_mode=False),datetime.now(timezone.utc)).step(measured=t,interval_seconds=1)
 assert s.soc_pct==50 and s.battery_current_a==-.2 and s.telemetry_origin=='software_test'
 assert s.battery_soc_method=='voltage_estimate' and s.battery_w==0
 assert s.battery_energy_kwh==pytest.approx(.004625)
 for extra in [dict(battery_current_a=float('nan')),dict(battery_soc_method='exact')]:
  with pytest.raises(ValueError):Esp32Telemetry(**(BASE|extra))


def test_water_api_interlocks_and_no_automatic_restart(tmp_path,monkeypatch):
 monkeypatch.setenv('SOC_OFFLINE','1')
 with TestClient(create_app(tmp_path/'house.sqlite3','house-key')) as c:
  s=c.get('/api/state').json()['settings'];c.put('/api/settings',json=s|{'demo_mode':False,'configured':True}).raise_for_status()
  h={'X-Device-Key':'house-key'};data=BASE|{'water':WATER}
  assert c.post('/api/water/command',json={'action':'manual'}).status_code==409
  c.put('/api/water/config',json={'enabled':True,'max_run_seconds':5,'filter_service_minutes':60}).raise_for_status()
  assert c.post('/api/device/telemetry',json=data).status_code==401
  c.post('/api/device/telemetry',json=data,headers=h).raise_for_status()
  c.post('/api/water/command',json={'action':'manual'}).raise_for_status()
  assert c.post('/api/device/telemetry',json=data,headers=h).json()['water_command']['pump_on']
  leak=data|{'water':WATER|{'leak_detected':True}}
  assert not c.post('/api/device/telemetry',json=leak,headers=h).json()['water_command']['pump_on']
  c.post('/api/device/telemetry',json=data,headers=h)
  assert c.post('/api/water/command',json={'action':'manual'}).status_code==409
  c.post('/api/water/command',json={'action':'reset'})
  reset=c.post('/api/device/telemetry',json=data,headers=h).json()['water_command']
  assert reset['reset_fault'] and not reset['pump_on']
  c.post('/api/water/command',json={'action':'manual'}).raise_for_status()
  c.post('/api/device/telemetry',json=data,headers=h)
  c.app.state.engine.water.started-=6
  assert not c.post('/api/device/telemetry',json=data,headers=h).json()['water_command']['pump_on']
  assert c.get('/api/water').json()['fault']=='timeout'
  assert c.get('/stavba/STAVEBNY-NAVOD.pdf').status_code==200
  assert c.get('/static/house/model.json').status_code==200
  # New fields survive storage/CSV; no synthetic SOC is fabricated for old devices.
  c.portal.call(c.app.state.engine.tick)
  text=c.get('/api/export').text
  assert 'battery_current_a' in text and 'software_test' in text
  assert c.post('/api/water/command',json={'action':'anything'}).status_code==422


def test_water_counters_do_not_mix_demo_with_hardware(tmp_path,monkeypatch):
 clock=[100.0];monkeypatch.setattr('backend.water.monotonic',lambda:clock[0])
 store=Storage(tmp_path/'water.sqlite3');w=WaterController(store)
 demo=Settings();w.action(WaterAction(action='manual'),demo,None,False)
 clock[0]+=1;w.tick(demo,None,False)
 assert w.demo_service_seconds==1 and w.service_seconds==0
 live=Settings(demo_mode=False);t=Esp32Telemetry(**(BASE|{'water':WATER|{'pump_running':True}}))
 clock[0]+=1;w.tick(live,t,True)
 assert w.service_seconds==1 and w.demo_service_seconds==1
 assert WaterController(store).mode=='off'
 store.connection.close()


def test_manufacturing_geometry_matches_cutting_list():
 asset=json.loads((ROOT/'frontend/house/model.json').read_text())
 assert asset['units']=='mm' and asset['base']==[600,450,8]
 assert (ROOT/'frontend/house/model.json').read_bytes()==(ROOT/'model-domu/3d/model.json').read_bytes()
 base=next(m for m in asset['meshes'] if m['name'].startswith('P01'))
 for axis,size in enumerate([600,450,8]):
  values=base['p'][axis::3];assert max(values)-min(values)==pytest.approx(size,abs=.01)
 roof=[m for m in asset['meshes'] if m['g']==1]
 assert len(roof)==10 and all(m['name'].startswith('ROOF') for m in roof)
 assert not any('furniture' in m['name'].lower() for m in asset['meshes'])
 assert max(v for m in asset['meshes'] if m['g']==2 for v in m['p'][0::3])<=-10
 assert min(v for m in asset['meshes'] if m['g']==11 for v in m['p'][0::3])>=610
 for m in asset['meshes']:
  if m['g'] in {3,4,5,6,7,8,9,10,16}:
   assert min(m['p'][0::3])>=380 and max(m['p'][0::3])<=530
   assert min(m['p'][1::3])>=257 and max(m['p'][1::3])<=389
 with (ROOT/'model-domu/rezaci-plan.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 assert next(r for r in rows if r['ID']=='P10')['dlzka_mm']=='504'
 assert next(r for r in rows if r['ID']=='P10')['kusy']=='2'
 assert 'width="600mm"' in (ROOT/'model-domu/vykresy/P01-1ku1.svg').read_text()


@pytest.mark.skipif(not shutil.which('g++'),reason='C++ compiler unavailable')
def test_same_local_guards_as_esp32(tmp_path):
 exe=tmp_path/'guards'
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror',str(Path(__file__).with_name('house_guard_test.cpp')),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
