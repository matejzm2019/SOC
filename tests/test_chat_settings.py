import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.assistant import relevant_facts, is_small_talk
from backend.models import ChatMessage


@pytest.fixture
def chat_app(tmp_path, monkeypatch):
    monkeypatch.setenv('SOC_OFFLINE','1')
    output = {'answer':'Navrhujem zmenu.','changes':{}}
    def respond(request):
        if request.url.path == '/api/tags':
            return httpx.Response(200,json={'models':[{'name':'qwen3:0.6b'}]})
        if request.url.path == '/api/chat':
            body = json.loads(request.content)
            if 'format' in body:
                assert body['format']['properties']['changes']['additionalProperties'] is False
            return httpx.Response(200,json={'message':{'content':json.dumps(output)},'done_reason':'stop'})
        return httpx.Response(503)
    app=create_app(tmp_path / 'db.sqlite3','secret',httpx.MockTransport(respond))
    with TestClient(app) as client:
        yield client, output


def test_chat_proposes_confirms_cancels_by_not_applying_and_preserves_history(chat_app):
    client,output=chat_app
    before=client.get('/api/state').json()
    output['changes']={'buy_price':.2}
    reply=client.post('/api/assistant/chat',json={'question':'Nastav cenu 0,20 €/kWh'}).json()
    assert reply['proposal']['changes'][0]['label']=='Nákup (€/kWh)'
    assert client.get('/api/state').json()['settings']==before['settings']
    applied=client.post('/api/assistant/apply',json={'token':reply['proposal']['token']})
    assert applied.status_code==200, applied.text
    state=applied.json()
    assert state['settings']['buy_price']==.2 and state['settings']['price_source']=='manual'
    assert client.get(f"/api/history?run_id={before['demo']['run_id']}").json()['sample_count']==288
    assert client.post('/api/assistant/apply',json={'token':reply['proposal']['token']}).status_code==410
    output['changes']={'price_source':'internet'}
    pending=client.post('/api/assistant/chat',json={'question':'Zapni internetove ceny'}).json()['proposal']
    assert pending and client.get('/api/state').json()['settings']['price_source']=='manual'
    output['changes']={}
    assert client.post('/api/assistant/chat',json={'question':'Kolko stoji energia?'}).json()['proposal'] is None


def test_stale_expired_and_tampered_proposals_do_not_change_settings(chat_app):
    client,output=chat_app
    output['changes']={'battery_capacity_mah':2000}
    reply=client.post('/api/assistant/chat',json={'question':'Nastav kapacitu clanku 2000 mAh'}).json()
    token=reply['proposal']['token']
    current=client.get('/api/state').json()
    client.put('/api/settings',json=current['settings'] | {'base_load_w':800}).raise_for_status()
    assert client.post('/api/assistant/apply',json={'token':token}).status_code==409
    assert client.get('/api/state').json()['settings']['battery_capacity_mah']==1000
    assert client.post('/api/assistant/apply',json={'token':token,'changes':{'buy_price':0}}).status_code==422
    proposal=client.post('/api/assistant/chat',json={'question':'Nastav kapacitu clanku 2000 mAh'}).json()['proposal']
    client.app.state.engine.chat_proposals[proposal['token']]['created']-=601
    assert client.post('/api/assistant/apply',json={'token':proposal['token']}).status_code==410


@pytest.mark.parametrize('changes',[{'buy_price':-1},{'price_source':'https://evil.example'},
                                   {'device_key':'secret'},{'demo_mode':'false'},{'buy_price':True}])
def test_invalid_model_changes_are_never_executable(chat_app,changes):
    client,output=chat_app
    before=client.get('/api/state').json()['settings']
    output['changes']=changes
    reply=client.post('/api/assistant/chat',json={'question':'Zmen nastavenia'}).json()
    assert reply['proposal'] is None and reply['answer']
    assert client.get('/api/state').json()['settings']==before


def test_chat_can_switch_demo_to_esp_and_enable_disabled_prices(chat_app):
    client,output=chat_app
    before=client.get('/api/state').json()
    client.put('/api/settings',json=before['settings'] | {'prices_enabled':False}).raise_for_status()
    output['changes']={'price_source':'internet','demo_mode':False}
    reply=client.post('/api/assistant/chat',json={'question':'Zapni internetove ceny a vypni demo'}).json()
    saved=client.post('/api/assistant/apply',json={'token':reply['proposal']['token']}).json()
    assert saved['settings']['prices_enabled'] and saved['settings']['price_source']=='internet'
    assert saved['settings']['measurement_source']=='hybrid' and not saved['demo']['enabled']
    assert client.get('/api/history').json()['sample_count']==0


def test_price_questions_and_followups_use_price_facts_without_unrelated_daily_cost():
    facts=[{'id':'F1','label':'Pôvod'}, {'id':'F2','label':'Vypočítané náklady v poslednom dni'},
           {'id':'F3','label':'Nákupná cena posledného intervalu'}, {'id':'F4','label':'Teplota'}]
    selected=relevant_facts('Koľko stojí energia?',[],facts)
    assert [f['id'] for f in selected]==['F1','F3']
    followup=relevant_facts('A teraz?', [ChatMessage(role='user',content='Koľko stojí energia?')],facts)
    assert followup==selected
    assert relevant_facts('Zhrň scenár.',[],facts)==facts


def test_small_talk_uses_llm_without_energy_facts_history_or_settings_classifier(tmp_path, monkeypatch):
    monkeypatch.setenv('SOC_OFFLINE','1')
    calls=[]
    def respond(request):
        if request.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':'qwen3:0.6b'}]})
        body=json.loads(request.content)
        calls.append(body)
        return httpx.Response(200,json={'message':{'content':'Ahoj! Ako ti môžem pomôcť?'},'done_reason':'stop'})
    with TestClient(create_app(tmp_path/'chat.sqlite3','secret',httpx.MockTransport(respond))) as client:
        for question in ('ahoj','Čau!','Dobrý deň.','Ahoj, ako sa máš?','ďakujem'):
            reply=client.post('/api/assistant/chat',json={'question':question,'history':[
                {'role':'user','content':'Koľko stojí energia?'},
                {'role':'assistant','content':'Výkon je 12345 kW.'}]}).json()
            assert reply['answer']=='Ahoj! Ako ti môžem pomôcť?'
            assert reply['facts']==[] and reply['proposal'] is None and not reply['truncated']
            body=calls[-1]
            assert 'format' not in body and len(body['messages'])==2
            assert '12345' not in body['messages'][0]['content'] and 'Nákupná cena' not in body['messages'][0]['content']
            assert body['options']['num_predict']==512 and body['think'] is False
        assert len(calls)==5
        before=client.get('/api/state').json()
        before=client.put('/api/settings',json=before['settings']).json()
        better=client.put('/api/settings',json=before['settings'] | {'ai_model':'qwen3:4b-instruct-2507-q4_K_M'})
        assert better.status_code==200 and better.json()['demo']['run_id']==before['demo']['run_id']
        status=client.get('/api/assistant/status?model=qwen3:4b-instruct-2507-q4_K_M')
        assert status.status_code==200 and not status.json()['available']
    assert not is_small_talk('Ahoj, zapni internetové ceny.')
    assert not is_small_talk('Ahoj, aký je výkon FV?')
