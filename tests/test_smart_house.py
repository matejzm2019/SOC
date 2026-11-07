import csv
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
from datetime import datetime,timezone
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.models import Esp32Telemetry,Settings
from backend.simulator import Simulator
from backend.storage import Storage

ROOT=Path(__file__).resolve().parents[1]
BASE=dict(panel_voltage_v=6,panel_current_a=.03,panel_power_w=.18,
          grid_available=True,load_stage=3,battery_voltage_v=3.8,battery_soc_pct=50,
          battery_current_a=-.2,battery_soc_method='voltage_estimate',telemetry_origin='software_test')


def test_house_telemetry_is_labelled_and_not_a_kw_battery():
 t=Esp32Telemetry(**BASE)
 s=Simulator(Settings(demo_mode=False),datetime.now(timezone.utc)).step(measured=t,interval_seconds=1)
 assert s.soc_pct==50 and s.battery_current_a==-.2 and s.telemetry_origin=='software_test'
 assert s.battery_soc_method=='voltage_estimate' and s.battery_w==0
 assert s.battery_energy_kwh==pytest.approx(.004625)
 for extra in [dict(battery_current_a=float('nan')),dict(battery_soc_method='exact')]:
  with pytest.raises(ValueError):Esp32Telemetry(**(BASE|extra))


def test_lighting_only_api(tmp_path,monkeypatch):
 monkeypatch.setenv('SOC_OFFLINE','1')
 with TestClient(create_app(tmp_path/'house.sqlite3','house-key')) as c:
  assert 'water' not in c.get('/api/state').json()
  assert c.get('/api/water').status_code==404
  assert c.post('/api/device/telemetry',json=BASE).status_code==401
  reply=c.post('/api/device/telemetry',json=BASE,headers={'X-Device-Key':'house-key'})
  assert reply.status_code==200 and 'water_command' not in reply.json()
  assert c.get('/stavba/STAVEBNY-NAVOD.pdf').status_code==200
  assert c.get('/static/house/model.json').status_code==200
  assert c.post('/api/device/telemetry',json=BASE|{'water':{}},headers={'X-Device-Key':'house-key'}).status_code==422


def test_manufacturing_geometry_matches_cutting_list():
 asset=json.loads((ROOT/'frontend/house/model.json').read_text())
 assert asset['units']=='mm' and asset['base']==[600,450,8]
 assert (ROOT/'frontend/house/model.json').read_bytes()==(ROOT/'model-domu/3d/model.json').read_bytes()
 base=next(m for m in asset['meshes'] if m['name'].startswith('P01'))
 for axis,size in enumerate([600,450,8]):
  values=base['p'][axis::3];assert max(values)-min(values)==pytest.approx(size,abs=.01)
 roof=[m for m in asset['meshes'] if m['g']==1]
 assert len(roof)>30 and all(m['name'].startswith('ROOF') for m in roof)
 assert not any('furniture' in m['name'].lower() for m in asset['meshes'])
 controls=[m for m in asset['meshes'] if m['g'] in (14,17)]
 assert all(25<=v<=132 for m in controls for v in m['p'][0::3])
 assert all(15<=v<=60 for m in controls for v in m['p'][1::3])
 # Neither the switches nor their service panel intersect the entrance path X323–385.
 assert max(v for m in controls for v in m['p'][0::3])<323
 guides=[m for m in asset['meshes'] if m['name'].startswith('ROOF L02')]
 assert all(max(m['p'][2::3])<=118 for m in guides)
 assert not any('460x10x10' in m['name'] for m in asset['meshes'])
 assert asset['roof_groups']==[1,2] and asset['roof_angle_deg']==35
 assert not any(m['g'] in {10,11} for m in asset['meshes'])
 panel=next(m for m in asset['meshes'] if m['name']=='SOLAR Panel 230x195x17')
 assert 180<min(panel['p'][0::3])<190 and 410<max(panel['p'][0::3])<420
 angle=math.radians(35);ridge=128+165*math.tan(angle)
 vertices=list(zip(panel['p'][0::3],panel['p'][1::3],panel['p'][2::3]))
 clearance=[-(y-235)*math.sin(angle)+(z-ridge)*math.cos(angle) for x,y,z in vertices]
 down_slope=[-(y-235)*math.cos(angle)-(z-ridge)*math.sin(angle) for x,y,z in vertices]
 assert min(clearance)>9.9 and max(clearance)<27.1
 assert min(down_slope)>15 and max(down_slope)<211
 assert all(0<=v<=600 for m in asset['meshes'] for v in m['p'][0::3])
 for m in asset['meshes']:
  if m['g'] in {3,4,5,6,7,8,9,16}:
   assert min(m['p'][0::3])>=380 and max(m['p'][0::3])<=530
   assert min(m['p'][1::3])>=257 and max(m['p'][1::3])<=389
 with (ROOT/'model-domu/rezaci-plan.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 assert next(r for r in rows if r['ID']=='P10')['dlzka_mm']=='504'
 assert next(r for r in rows if r['ID']=='P10')['kusy']=='2'
 assert next(r for r in rows if r['ID']=='P10')['sirka_mm']=='230'
 assert not any(r['ID'] in {'P12','P13','P14'} for r in rows)
 assert 'width="600mm"' in (ROOT/'model-domu/vykresy/P01-1ku1.svg').read_text()


@pytest.mark.skipif(not shutil.which('g++'),reason='C++ compiler unavailable')
def test_same_local_guards_as_esp32(tmp_path):
 exe=tmp_path/'guards'
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror',str(Path(__file__).with_name('house_guard_test.cpp')),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
