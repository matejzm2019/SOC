import json
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.models import Settings
from backend.assistant_tools import AssistantTools,WeatherArgs
from backend import assistant_tools,weather

FIXED=datetime(2026,11,8,23,30,tzinfo=timezone.utc)
class Clock(datetime):
 @classmethod
 def now(cls,tz=None):return FIXED.astimezone(tz or timezone.utc)

def forecast(zone='Europe/Bratislava',offset=0):
 start=FIXED.replace(hour=0,minute=0,second=0,microsecond=0)
 stamps=[int((start+timedelta(hours=i)).timestamp()) for i in range(168)]
 temps=[float(datetime.fromtimestamp(t,ZoneInfo(zone)).day+offset) for t in stamps]
 hourly={'time':stamps,'temperature_2m':temps,'cloud_cover':[20]*168,'wind_speed_10m':[2]*168,
  'shortwave_radiation':[100]*168,'global_tilted_irradiance':[120]*168,'precipitation':[0]*168,'weather_code':[1]*168}
 current={k:v[0] for k,v in hourly.items()};current['time']=int(FIXED.timestamp())
 return {'timezone':zone,'current':current,'hourly':hourly}

@pytest.fixture(autouse=True)
def frozen(monkeypatch):
 monkeypatch.setenv('SOC_OFFLINE','1');monkeypatch.delenv('OLLAMA_API_KEY',raising=False)
 monkeypatch.setattr(assistant_tools,'datetime',Clock);monkeypatch.setattr(weather,'datetime',Clock)

def configure(c,**extra):
 s=c.get('/api/state').json()['settings'];s.update(ai_model='qwen3:4b',location_set=True,location_name='Bratislava',**extra)
 return c.put('/api/settings',json=s).json()['settings']

def test_tomorrow_is_local_calendar_day_even_when_dashboard_weather_disabled(tmp_path):
 calls=[]
 def respond(r):
  calls.append(r)
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:4b'}]})
  if r.url.host=='api.open-meteo.com':
   assert r.url.params['forecast_days']=='7' and r.url.params['timezone']=='auto'
   return httpx.Response(200,json=forecast())
  body=json.loads(r.content);assert 'format' not in body and body['options']['num_ctx']==8192
  prompt=body['messages'][0]['content']
  assert 'Zajtra 2026-11-10 – teplota vzduchu' in prompt and 'Zajtra o 12:00' in prompt
  return httpx.Response(200,json={'message':{'content':'Zajtra v Bratislave očakávaj minimum 10.0 °C a maximum 10.0 °C.'}})
 app=create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))
 with TestClient(app) as c:
  before=configure(c,weather_enabled=False,weather_source='simulator')
  checked=c.get('/api/assistant/status?model=qwen3:4b');assert checked.status_code==200 and checked.json()['available']
  reply=c.post('/api/assistant/chat',json={'question':'Aká bude zajtra teplota?'}).json()
  assert reply['numeric_guard_passed'] and '10.0 °C' in reply['answer']
  assert reply['sources'][0]['kind']=='weather' and reply['proposal'] is None
  assert c.get('/api/state').json()['settings']==before
  assert app.state.engine.weather.snapshot is None
  # Forecast is served from the private assistant cache on repeat.
  c.post('/api/assistant/chat',json={'question':'Aká bude zajtra teplota?'})
  assert sum(r.url.host=='api.open-meteo.com' for r in calls)==1

@pytest.mark.parametrize('question,history', [('A zajtra?',[{'role':'user','content':'Aké je počasie v Tokiu?'}]),('Aké bude zajtra počasie v Tokiu?',[])])
def test_city_tool_followup_uses_location_timezone_without_changing_home(tmp_path,question,history):
 calls=[];model_calls=[0]
 def respond(r):
  calls.append(r)
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:4b'}]})
  if r.url.host=='geocoding-api.open-meteo.com':return httpx.Response(200,json={'results':[{'name':'Tokio','country':'Japonsko','latitude':35.676,'longitude':139.65}]})
  if r.url.host=='api.open-meteo.com':return httpx.Response(200,json=forecast('Asia/Tokyo',10))
  body=json.loads(r.content);model_calls[0]+=1
  if model_calls[0]==1:
   return httpx.Response(200,json={'message':{'content':'','tool_calls':[{'function':{'name':'weather_forecast','arguments':{'city':'Tokyo','day':'tomorrow','hour':14}}}]}})
  result=json.loads(body['messages'][-1]['content']);assert result['timezone']=='Asia/Tokyo'
  assert result['days'][0]['date']=='2026-11-10' and result['days'][0]['max_c']==20
  assert any('14:00' in f['label'] for f in result['facts'])
  return httpx.Response(200,json={'message':{'content':'V Tokiu bude zajtra maximum 20.0 °C.'}})
 app=create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))
 with TestClient(app) as c:
  before=configure(c)
  reply=c.post('/api/assistant/chat',json={'question':question,'history':history}).json()
  assert reply['numeric_guard_passed'] and '20.0 °C' in reply['answer']
  assert c.get('/api/state').json()['settings']==before and app.state.engine.weather.snapshot is None
  assert len([x for x in calls if x.url.host=='geocoding-api.open-meteo.com'])==1
  assert len([x for x in calls if x.url.host=='api.open-meteo.com'])==1

def test_missing_town_and_disabled_lookup_never_invent_forecast(tmp_path):
 external=[]
 def respond(r):
  if r.url.host!='127.0.0.1':external.append(r)
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:0.6b'}]})
  return httpx.Response(200,json={'message':{'content':'Pre ktoré mesto chceš predpoveď?'}})
 with TestClient(create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))) as c:
  reply=c.post('/api/assistant/chat',json={'question':'Bude zajtra teplo?'}).json()
  assert not reply['sources'] and not external
  s=c.get('/api/state').json()['settings'];s['ai_online_enabled']=False
  c.put('/api/settings',json=s)
  reply=c.post('/api/assistant/chat',json={'question':'Aká bude teplota zajtra?'}).json()
  assert not reply['online_used'] and not external

def test_general_knowledge_keeps_scientific_numbers_and_skips_settings_classifier(tmp_path):
 bodies=[]
 def respond(r):
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:0.6b'}]})
  body=json.loads(r.content);bodies.append(body)
  return httpx.Response(200,json={'message':{'content':'Pri bežnom atmosférickom tlaku voda vrie pri 100 °C.'}})
 with TestClient(create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))) as c:
  reply=c.post('/api/assistant/chat',json={'question':'Pri akej teplote vrie voda?'}).json()
  assert '100 °C' in reply['answer'] and reply['basis']=='general_knowledge'
  assert len(bodies)==1 and 'format' not in bodies[0] and reply['proposal'] is None

def test_web_tool_preserves_source_links_and_labels_encyclopedia_fallback(tmp_path):
 count=[0]
 def respond(r):
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:0.6b'}]})
  if r.url.host=='html.duckduckgo.com':return httpx.Response(202,text='<form>captcha</form>')
  if r.url.host=='sk.wikipedia.org':return httpx.Response(200,json={'query':{'pages':{'1':{'title':'FreeRTOS','extract':'FreeRTOS je operačný systém reálneho času.','fullurl':'https://sk.wikipedia.org/wiki/FreeRTOS'}}}})
  body=json.loads(r.content);count[0]+=1
  if count[0]==1:return httpx.Response(200,json={'message':{'tool_calls':[{'function':{'name':'search_web','arguments':{'query':'FreeRTOS'}}}]}})
  data=json.loads(body['messages'][-1]['content']);assert data['scope']=='encyclopedia' and data['notice']
  return httpx.Response(200,json={'message':{'content':'Podľa Wikipédie je FreeRTOS operačný systém reálneho času.'}})
 with TestClient(create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))) as c:
  reply=c.post('/api/assistant/chat',json={'question':'Nájdi zdroj o FreeRTOS'}).json()
  assert reply['sources'][0]['url']=='https://sk.wikipedia.org/wiki/FreeRTOS'
  assert reply['sources'][0]['scope']=='encyclopedia' and reply['online_used']

def test_tool_budget_rejects_unknown_functions_without_running_or_writing(tmp_path):
 count=[0]
 def respond(r):
  assert r.url.host=='127.0.0.1'
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:0.6b'}]})
  count[0]+=1
  return httpx.Response(200,json={'message':{'tool_calls':[{'function':{'name':'run_shell','arguments':{'cmd':'bad'}}}]}})
 with TestClient(create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))) as c:
  before=c.get('/api/state').json()['settings']
  reply=c.post('/api/assistant/chat',json={'question':'Nájdi vysvetlenie'}).json()
  assert count[0]==4 and reply['proposal'] is None and not reply['sources']
  assert c.get('/api/state').json()['settings']==before


def test_installed_4b_is_used_when_default_small_model_is_missing(tmp_path):
 def respond(r):
  if r.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'qwen3:4b'}]})
  body=json.loads(r.content);assert body['model']=='qwen3:4b' and body['options']['num_ctx']==8192
  return httpx.Response(200,json={'message':{'content':'Fotosyntéza premieňa svetelnú energiu na chemickú.'}})
 with TestClient(create_app(tmp_path/'db.sqlite3','test',httpx.MockTransport(respond))) as c:
  state=c.get('/api/state').json()
  reply=c.post('/api/assistant/chat',json={'question':'Čo je fotosyntéza?'}).json()
  assert reply['model']=='qwen3:4b' and reply['proposal'] is None
  settings=state['settings']|{'ai_online_enabled':False}
  saved=c.put('/api/settings',json=settings).json()
  # Initial configured flag may be stored; changing AI options never resets physics.
  again=c.put('/api/settings',json=saved['settings']|{'ai_online_enabled':True}).json()
  assert saved['demo']['run_id']==again['demo']['run_id']
  assert c.get('/api/state').json()['settings']['ai_model']==state['settings']['ai_model']
