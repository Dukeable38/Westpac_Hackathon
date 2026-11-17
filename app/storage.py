"""Local demo records. Uploaded PDF bytes are not retained after processing."""
import json,sqlite3,uuid
from pathlib import Path
from datetime import datetime,timezone
from .seed import ROOT,SEED
import os
DB=Path(os.getenv('RADAR_DB')) if os.getenv('RADAR_DB') else ROOT/'app/db.sqlite'

def connect():
    db=sqlite3.connect(DB,timeout=5)
    db.execute('CREATE TABLE IF NOT EXISTS receipts (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
    for customer in SEED['customers']:
        # Seed corrections must replace stale demo profiles after an upgrade.
        # This updates only seeded customer rows, never decision receipts.
        db.execute('INSERT INTO customers VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',(customer['id'],json.dumps(customer)))
    db.commit()
    return db

def receipt(result,decision):
    # Decision 17 Nov 2026 (Kiel): no file name is stored, only the SHA-256 fingerprint of the checked PDF.
    # Payee, amount and invoice number identify the payment row; the hash proves which exact file was checked.
    record={k:result[k] for k in ['customer_id','sha256','score','band','level']}
    ex=result.get('extracted') or {}
    pm=(ex.get('payment_methods') or [{}])[0]
    record.update(payee=ex.get('supplier_name',''),amount=ex.get('total',0),invoice_number=ex.get('invoice_number',''),
                  pay_to=(f"{pm.get('bsb','')} {pm.get('account_number','')}".strip() if pm.get('bsb') else pm.get('payid') or pm.get('biller_code') or ''))
    record.update(receipt_id=uuid.uuid4().hex,decision=decision,decided_at=datetime.now(timezone.utc).isoformat(),signals_summary=result['signals'],pdf_stored=False,file_name_stored=False)
    with connect() as db: db.execute('INSERT INTO receipts VALUES (?,?)',(record['receipt_id'],json.dumps(record)))
    return record

def receipts(customer_id):
    with connect() as db: rows=[json.loads(r[0]) for r in db.execute('SELECT data FROM receipts')]
    rows=[r for r in rows if r.get('customer_id')==customer_id]
    return sorted(rows,key=lambda r:r.get('decided_at',''),reverse=True)

def get_receipt(receipt_id):
    with connect() as db: row=db.execute('SELECT data FROM receipts WHERE id=?',(receipt_id,)).fetchone()
    return json.loads(row[0]) if row else None
