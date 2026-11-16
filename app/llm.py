"""Provider boundary: inputs must already be sanitised; outputs are not policy."""
import re
from .models import InvoiceJSON, PaymentMethod

def _match(pattern, text, default=''):
    m = re.search(pattern,text,re.I|re.M)
    return m.group(1).strip() if m else default

def extract(sanitised_text):
    t = sanitised_text
    abn = re.sub(r'\D','',''.join(re.findall(r'ABN\s*([\d ]{11,15})',t,re.I)[-1:]))
    emails = re.findall(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}',t,re.I)
    email = emails[-1] if emails else ''
    def money(label):
        return float(_match(label+r'[^\n$]*\$([\d,]+\.\d{2})',t,'0').replace(',',''))
    name = _match(r'Account name\s*([^\n]+)',t) or _match(r'^(.+?(?:Co\.|Hire|Pty Ltd))',t)
    bsb = _match(r'BSB\s*(\d{3}[- ]?\d{3})',t)
    account = re.sub(r'\s','',_match(r'^Acc?ount\s+(\d[\d ]{5,15})$',t))
    method = PaymentMethod(type='BPAY' if 'BPAY' in t.upper() else 'BSB',bsb=bsb,account_number=account,account_name=name,biller_code=_match(r'Biller code\s*(\d+)',t))
    return InvoiceJSON(supplier_name=name,abn=abn,email=email,phone=_match(r'(0[2378] \d{4} \d{4})',t),website=_match(r'^([a-z0-9.-]+\.com\.au)$',t),invoice_number=_match(r'(INV-[\w-]+)',t),invoice_date=_match(r'^Date\s+([^\n]+)',t),due_date=_match(r'^Due\s+([^\n]+)',t),subtotal=money('Subtotal'),gst=money(r'GST'),total=money(r'Total due'),payment_methods=[method],free_text_notes=[line for line in t.splitlines() if any(w in line.lower() for w in ['changed','urgent','24 hours','first customers','overdue'])])

def classify(question, choices, snippet):
    s=snippet.lower()
    rules={'NEW_BUSINESS':['new business','met the owner','first customers'], 'ORDERED_THIS':['ordered this','placed the order'], 'SUPPLIER_CHANGED_BANKS':['changed banks','banking details have changed','bank details have changed'], 'VERIFIED_BY_PHONE_KNOWN_NUMBER':['usual number','known number'], 'SOLE_TRADER':['sole trader'], 'TRADING_NAME':['trading name'], 'YES':['urgent','24 hours','immediately','changed']}
    return next((c for c in choices if any(k in s for k in rules.get(c,[]))), 'NONE' if 'NONE' in choices else choices[-1])

def summarise(question, page_text):
    return page_text[:1000]
