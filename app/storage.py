"""Local demo records. Uploaded PDF bytes are not retained after processing."""
import json,sqlite3,uuid
from datetime import datetime,timezone
from .seed import ROOT,SEED
DB=ROOT/'app/db.sqlite'

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
    record={k:result[k] for k in ['customer_id','file_name','sha256','score','band','level']}
    record.update(receipt_id=uuid.uuid4().hex,decision=decision,decided_at=datetime.now(timezone.utc).isoformat(),signals_summary=result['signals'],pdf_stored=False)
    with connect() as db: db.execute('INSERT INTO receipts VALUES (?,?)',(record['receipt_id'],json.dumps(record)))
    return record
