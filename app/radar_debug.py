"""Radar debug screen: serves the live signal map and the data it needs.

GET /radar               the debug screen (app/static/radar.html)
GET /api/signals         every check from app/checks/catalogue.json plus current weights and tier budgets
GET /api/checks/latest   id of the most recent check, so the debug screen can follow checks started elsewhere

The screen animates the existing SSE stream (GET /api/check/{id}/events). It reads the catalogue at request
time, so adding or changing a check in catalogue.json shows up without touching the front end.
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from .seed import ROOT
from .score import CONFIG

router = APIRouter()

TIERS = [
    {'tier': 0, 'name': 'Instant', 'budget': '<300 ms · ~$0', 'runs': 'always'},
    {'tier': 1, 'name': 'Red flags', 'budget': '1–3 s · <1¢', 'runs': 'always'},
    {'tier': 2, 'name': 'Research', 'budget': '5–15 s · cents', 'runs': 'on escalation'},
    {'tier': 3, 'name': 'Deep', 'budget': '15–60 s+', 'runs': 'high value or still unsure'},
]


@router.get('/radar')
def radar_page():
    return FileResponse(ROOT / 'app/static/radar.html')


@router.get('/api/signals')
def signals():
    catalogue = json.loads((ROOT / 'app/checks/catalogue.json').read_text(encoding='utf-8'))
    out = []
    for cid, meta in catalogue.items():
        out.append({'id': cid, **meta,
                    'weight': CONFIG['weights'].get(cid),
                    'reassuring_weight': CONFIG.get('reassuring', {}).get(cid)})
    return {'tiers': TIERS, 'signals': out}


@router.get('/api/checks/latest')
def latest_check():
    from .main import RESULTS  # imported lazily: main.py includes this router
    if not RESULTS:
        raise HTTPException(404, 'No checks yet')
    check_id = next(reversed(RESULTS))
    r = RESULTS[check_id]
    return {'check_id': check_id, 'file_name': r.get('file_name'), 'score': r.get('score'), 'band': r.get('band')}
