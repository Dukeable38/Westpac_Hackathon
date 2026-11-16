"""Offline regression for a real-world ABN collision removed from fictional seed.

Audit evidence is point-in-time. These tests do not perform live registry calls.
"""
import json
from app.seed import ROOT,SEED
from app.checks.identifiers import abn_valid
from app.storage import connect

def test_seed_abns_have_absent_registry_audit():
    audit=json.loads((ROOT/'demo/seed/abn-audit.json').read_text())
    checked={r['abn']:r for r in audit['records']}
    assert set(SEED['abn_registry'])==set(checked)
    assert '80310379062' not in SEED['abn_registry']
    for abn,record in checked.items():
        assert abn_valid(abn)
        assert record['result']=='ABN not found: no record matching this ABN'
        assert record['url']==f'https://abr.business.gov.au/ABN/View?abn={abn}'
    corella=next(s for s in SEED['customers'][0]['suppliers'] if s['supplier_id']=='sup_corella')
    assert corella['abn']=='93270000491'

def test_database_seed_refreshes_corrected_abn_without_deleting_receipts():
    with connect() as db:
        receipts_before=db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]
        stored=json.loads(db.execute('SELECT data FROM customers WHERE id=?',('cust_greenline',)).fetchone()[0])
        corella=next(s for s in stored['suppliers'] if s['supplier_id']=='sup_corella')
        corella['abn']='80310379062'
        db.execute('UPDATE customers SET data=? WHERE id=?',(json.dumps(stored),'cust_greenline'))
    with connect() as db:
        refreshed=json.loads(db.execute('SELECT data FROM customers WHERE id=?',('cust_greenline',)).fetchone()[0])
        assert next(s for s in refreshed['suppliers'] if s['supplier_id']=='sup_corella')['abn']=='93270000491'
        assert db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]==receipts_before
