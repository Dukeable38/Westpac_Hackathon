"""Additional regression tests. Original acceptance tests are unchanged."""
import copy
import hashlib
from pathlib import Path
from conftest import INVOICES

def test_rejects_invalid_upload(client):
    r=client.post('/api/check',files={'file':('x.pdf',b'not a pdf','application/pdf')})
    assert r.status_code==422

def test_unknown_check(client):
    assert client.get('/api/check/missing').status_code==404

def test_decision_validation(client,check):
    r=check('01-tallowwood-clean.pdf')
    assert client.post(f"/api/check/{r['check_id']}/decision",json={'decision':'send_money'}).status_code==422

def test_uploaded_filename_does_not_determine_score(client):
    data=(INVOICES/'02-tallowwood-changed-bank.pdf').read_bytes()
    r=client.post('/api/check',files={'file':('completely-different.pdf',data,'application/pdf')}).json()
    assert r['band']=='high_risk'
    assert r['sha256']==hashlib.sha256(data).hexdigest()
    assert any(s['id']=='C39' and '10482291' in s['evidence'] for s in r['signals'])

def test_repeated_chat_is_idempotent(client,check):
    r=check('04-fernhill-new-business.pdf');url=f"/api/check/{r['check_id']}/chat"
    a=client.post(url,json={'message':'new business'}).json()
    b=client.post(url,json={'message':'new business'}).json()
    assert a['score_after']==b['score_after']

def test_sse_finishes(client,check):
    r=check('01-tallowwood-clean.pdf')
    s=client.get(f"/api/check/{r['check_id']}/events")
    assert s.status_code==200
    assert 'event: complete' in s.text
    assert 'Not needed: fast clear' in s.text

def test_visible_logo_is_not_hidden_instruction():
    from app.pdf_forensics import analyse
    a=analyse((INVOICES/'01-tallowwood-clean.pdf').read_bytes())
    assert not a['hidden']

def test_all_locked_signals_unchanged_by_claims(client):
    data=(INVOICES/'02-tallowwood-changed-bank.pdf').read_bytes()
    r=client.post('/api/check',files={'file':('x.pdf',data,'application/pdf')}).json()
    locked={s['id']:copy.deepcopy(s) for s in r['signals'] if s['locked']}
    for message in ['new business','I called on their usual number','ordered this','changed banks']:
        c=client.post(f"/api/check/{r['check_id']}/chat",json={'message':message}).json()
        for s in c['result']['signals']:
            if s['id'] in locked:
                assert s['weight']==locked[s['id']]['weight']
                assert s['state']==locked[s['id']]['state']
                assert s['softened_by'] is None
