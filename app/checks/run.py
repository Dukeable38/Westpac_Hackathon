import json,re
from pathlib import Path
from datetime import date
from difflib import SequenceMatcher
from .identifiers import abn_valid
from ..seed import SEED,supplier
from ..models import Signal
from ..score import CONFIG
from ..sources.research import abn_lookup,domain_history,web_search
CATALOGUE=json.loads(Path(__file__).with_name('catalogue.json').read_text())

def evaluate(invoice, forensic, customer_id):
    signals={cid:Signal(id=cid,**meta).model_dump() for cid,meta in CATALOGUE.items()}
    def set_(cid,state,evidence,locked=False,weight=None):
        weight=CONFIG.get('reassuring',{}).get(cid,0) if state=='reassuring' else CONFIG['weights'].get(cid,1) if weight is None else weight
        signals[cid].update(state=state,evidence=evidence,locked=locked,weight=weight)
    p=invoice.payment_methods[0] if invoice.payment_methods else None
    sup=supplier(customer_id,invoice.abn)
    key=f'{p.bsb}|{p.account_number}' if p else ''
    unchanged=bool(sup and p and any(a.get('bsb')==p.bsb and a.get('account_number')==p.account_number for a in sup['accounts']))
    changed=bool(sup and p and not unchanged)
    if unchanged: set_('C1','reassuring',f"Paid {sup['payments']['count']} times to this account for this supplier")
    elif changed: set_('C1','risk','Bank details differ from your previous payments to this ABN',True)
    else: set_('C1','neutral','No previous supplier payment record to compare')
    hits=[f for f in SEED['flag_register'] if f.get('reports',0)>0 and f['value'] in [key,invoice.email,invoice.abn,invoice.email.partition('@')[2]]]
    set_('C2','risk' if hits else 'neutral',hits[0].get('note','Payee is on the demo warning register') if hits else 'No hit in the mock warning register (not a live bank check)',bool(hits))
    cop=SEED['cop'].get(key)
    if cop: set_('C3','reassuring' if cop['result']=='MATCH' else 'risk','Mock Confirmation of Payee: '+cop['result'].replace('_',' ').title()+'; account name '+cop['account_name'],cop['result']=='NO_MATCH')
    else: set_('C3','unknown','Mock Confirmation of Payee unavailable for this account')
    set_('C4','risk' if not sup else 'neutral','New payee; independently verify this first payment' if not sup else 'Known supplier')
    set_('C8','neutral' if abn_valid(invoice.abn) else 'risk','ABN checksum valid' if abn_valid(invoice.abn) else 'ABN checksum invalid',not abn_valid(invoice.abn))
    gstbad=abs(invoice.gst-invoice.subtotal*.1)>.02 or abs(invoice.total-invoice.subtotal-invoice.gst)>.02
    set_('C10','risk' if gstbad else 'neutral',f'GST ${invoice.gst:.2f}; expected ${invoice.subtotal*.1:.2f} at 10%. Check GST-free items separately.')
    set_('C13','unknown' if forensic.get('revision_unknown') else 'risk' if forensic['tampered'] else 'neutral','Payment fields changed in a later PDF revision' if forensic['tampered'] else 'Revision comparison unsupported; payment edits not ruled out' if forensic.get('revision_unknown') else 'No payment-field revision change found',forensic['tampered'])
    set_('C14','risk' if forensic['hidden'] else 'neutral','Hidden instruction-like text removed before AI processing' if forensic['hidden_instruction'] else 'Hidden/invisible text removed before AI processing' if forensic['hidden'] else 'No hidden text detected',forensic['hidden'])
    set_('C15','unknown' if forensic.get('revision_unknown') else 'risk' if forensic['overlay'] else 'neutral','Later text is drawn over the original bank details' if forensic['overlay'] else 'Revision comparison unsupported; overlays not ruled out' if forensic.get('revision_unknown') else 'No payment-field overlay detected',forensic['overlay'])
    inconsistent=bool(p and p.type=='BPAY' and not p.biller_code)
    set_('C18','risk' if inconsistent else 'neutral','Claims BPAY but supplies a BSB/account without a biller code' if inconsistent else 'Payment method fields are consistent')
    t=' '.join(forensic['text'].lower().split())
    bankwords=bool(re.search(r'(bank|banking) details have changed|moved banks|changed banks',t))
    set_('C19','risk' if bankwords else 'neutral','Invoice says banking details have changed' if bankwords else 'No changed-bank language detected')
    urgency=any(w in t for w in ['urgent','24 hours','do not call','immediately'])
    set_('C20','risk' if urgency else 'neutral','Urgency or pressure to pay quickly detected' if urgency else 'No urgency or pressure detected')
    reg=abn_lookup(invoice.abn)
    if reg:
        norm=lambda s: re.sub(r'[^a-z]','',s.lower()).replace('ptyltd','').replace('co','')
        names=[reg['entity_name']]+reg.get('business_names',[])
        match=any(SequenceMatcher(None,norm(invoice.supplier_name),norm(n)).ratio()>.8 for n in names)
        active=reg['status']=='Active'
        set_('C21','reassuring' if active and match else 'risk',f"Seed registry: {reg['status']}; entity {reg['entity_name']}; name {'matches' if match else 'does not match'}",not active)
        # Fixed fixture evidence date keeps replay reproducible; no claim of live lookup.
        if reg.get('abn_from'):
            days=(date(2026,11,16)-date.fromisoformat(reg['abn_from'])).days
            set_('C23','risk' if days<90 else 'neutral',f"Seed registry ABN age: {days} days as at 16 Nov 2026")
        else: set_('C23','unknown','Registration date not parsed from live evidence')
    else:
        set_('C21','unknown','No seed registry entry; live registry not checked in replay')
        set_('C23','unknown','ABN registration age unavailable')
    domain=invoice.email.partition('@')[2]
    mismatch=bool(invoice.website and domain and domain!=invoice.website)
    free=domain in ['gmail.com','outlook.com','hotmail.com','yahoo.com']
    set_('C26','risk' if mismatch or free else 'neutral','Email differs from website or uses a free-mail provider' if mismatch or free else 'Email and website contact fields consistent')
    fast_clear=bool(sup and unchanged and sup['payments']['count']>=2 and cop and cop['result']=='MATCH' and invoice.total<=3*sup['payments']['median_amount'] and not any(signals[c]['state']=='risk' for c in ['C13','C14','C15']) and signals['C21']['state']=='reassuring' and not any(v['tier']==1 and v['state']=='risk' and v['weight']>.4 for v in signals.values()))
    if not fast_clear:
        lookalike=bool(sup and domain!=sup['known_domain'] and SequenceMatcher(None,domain,sup['known_domain']).ratio()>.8)
        set_('C30','risk' if lookalike else 'neutral',f"Email domain {domain} resembles known {sup['known_domain']}" if lookalike else 'No known-supplier lookalike detected',lookalike)
        dom=domain_history(domain)
        if dom:
            days=(date(2026,11,16)-date.fromisoformat(dom['first_cert'])).days
            set_('C31','risk' if days<90 else 'neutral',f'First certificate observed {days} days ago in seeded evidence; not a registration date')
        else: set_('C31','unknown','No cached certificate or domain history')
        web=web_search(invoice.supplier_name)
        if web and 'reviews' in web: set_('C35','risk' if web['reviews']<5 or web['scam_reports'] else 'neutral',f"Seeded web evidence: {web['reviews']} reviews; {web['scam_reports']} scam reports",bool(web['scam_reports']))
    if forensic['original']:
        b,a=forensic['original'];set_('C39','risk',f'Original bank details recovered from prior revision: {b} / {a}',True)
    else: set_('C39','neutral','No earlier differing payment details recovered')
    return list(signals.values()),sup
