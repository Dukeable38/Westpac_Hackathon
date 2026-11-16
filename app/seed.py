import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads((ROOT/'demo/seed/seed.json').read_text(encoding='utf-8'))

def supplier(customer_id, abn):
    customer = next((c for c in SEED['customers'] if c['id']==customer_id), {})
    return next((s for s in customer.get('suppliers',[]) if s['abn']==abn), None)
