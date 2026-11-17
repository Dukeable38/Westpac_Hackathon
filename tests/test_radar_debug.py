"""The /radar debug screen and the data it reads."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_signals_endpoint_serves_full_catalogue():
    data = client.get('/api/signals').json()
    assert len(data['tiers']) == 4
    ids = {s['id'] for s in data['signals']}
    assert {'C1', 'C13', 'C39'} <= ids
    for s in data['signals']:
        assert s['description'] and s['tier'] in (0, 1, 2, 3)
        assert all(f in ids for f in s.get('feeds', [])), f"{s['id']} feeds an unknown check"


def test_radar_page_and_latest_check():
    assert client.get('/radar').status_code == 200
    with open('demo/invoices/01-tallowwood-clean.pdf', 'rb') as f:
        check_id = client.post('/api/check', files={'file': ('01.pdf', f, 'application/pdf')}).json()['check_id']
    assert client.get('/api/checks/latest').json()['check_id'] == check_id
