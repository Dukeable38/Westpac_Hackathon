import json,re
from pathlib import Path
from datetime import date
from difflib import SequenceMatcher
from .additional import SKELETON_CHECKS,c25_government_allowlist,c41_human_referral,c52_bpay_consistency,chronology,foreign_currency,name_matches,relationship_state,suspicious_metadata
from .identifiers import abn_valid,acn_valid
from ..seed import SEED,supplier
from ..models import Signal
from ..score import CONFIG
from ..sources.research import abn_lookup,dns_posture,domain_history,web_search
CATALOGUE=json.loads(Path(__file__).with_name('catalogue.json').read_text())

def evaluate(invoice, forensic, customer_id, max_tier=3):
    signals={cid:Signal(id=cid,**meta).model_dump() for cid,meta in CATALOGUE.items()}
    for signal in signals.values():
        if signal['tier']>max_tier:
            signal.update(applicable=False,disposition='skipped',evidence='Not run: awaiting tier gate')
    def set_(cid,state,evidence,locked=False,weight=None,applicable=True,disposition=None):
        if signals[cid]['tier']>max_tier:return
        weight=CONFIG.get('reassuring',{}).get(cid,0) if state=='reassuring' else CONFIG['weights'].get(cid,1) if weight is None else weight
        disposition=disposition or ('not_applicable' if not applicable else 'unavailable' if state=='unknown' else 'checked')
        signals[cid].update(state=state,evidence=evidence,locked=locked,weight=weight,applicable=applicable,disposition=disposition)
    p=invoice.payment_methods[0] if invoice.payment_methods else None
    sup=supplier(customer_id,invoice.abn)
    customer=next((c for c in SEED['customers'] if c['id']==customer_id),{})
    key=f'{p.bsb}|{p.account_number}' if p else ''
    for cid,check in SKELETON_CHECKS.items():set_(cid,'unknown','Not checked: '+check())
    government=bool(re.search(r'\b(ato|australian taxation office|government)\b',invoice.supplier_name,re.I))
    set_('C25','unknown','Not checked: '+c25_government_allowlist() if government else 'Not applicable: supplier does not claim to be a government entity',applicable=government)
    set_('C41','unknown','Not applicable: '+c41_human_referral(),applicable=False)
    bpay=bool(p and p.type=='BPAY')
    set_('C52','unknown','Not checked: '+c52_bpay_consistency() if bpay else 'Not applicable: payment method is not BPAY',applicable=bpay)
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
    if sup:
        anomaly=invoice.total>3*sup['payments']['median_amount']
        set_('C7','risk' if anomaly else 'neutral',f"Amount ${invoice.total:.2f}; supplier median ${sup['payments']['median_amount']:.2f}; anomaly threshold 3× median",weight=.4)
    else:set_('C7','unknown','No supplier payment history for amount comparison')
    set_('C8','neutral' if abn_valid(invoice.abn) else 'risk','ABN checksum valid' if abn_valid(invoice.abn) else 'ABN checksum invalid',not abn_valid(invoice.abn))
    if invoice.acn:set_('C9','neutral' if acn_valid(invoice.acn) else 'risk','ACN checksum valid' if acn_valid(invoice.acn) else 'ACN checksum invalid',not acn_valid(invoice.acn))
    else:set_('C9','unknown','Not applicable: no ACN printed on invoice',applicable=False)
    gstbad=abs(invoice.gst-invoice.subtotal*.1)>.02 or abs(invoice.total-invoice.subtotal-invoice.gst)>.02
    set_('C10','risk' if gstbad else 'neutral',f'GST ${invoice.gst:.2f}; expected ${invoice.subtotal*.1:.2f} at 10%. Check GST-free items separately.')
    if p and p.bsb:
        valid_format=bool(re.fullmatch(r'\d{3}-?\d{3}',p.bsb))
        bank=SEED['bsb_directory'].get(p.bsb)
        if not valid_format:set_('C11','risk','BSB does not contain six digits',True)
        elif bank:set_('C11','neutral','BSB found in demo directory: '+bank+'; invoice does not assert a bank name to compare')
        else:set_('C11','unknown','BSB format valid but not in the small demo directory; not evidence of invalidity')
    else:set_('C11','unknown','No BSB provided for directory comparison')
    editor=suspicious_metadata(forensic.get('metadata',{}))
    set_('C12','risk' if editor else 'neutral',f'PDF metadata shows online editor: {editor}' if editor else 'No high-risk PDF editor found in metadata')
    set_('C13','unknown' if forensic.get('revision_unknown') else 'risk' if forensic['tampered'] else 'neutral','Payment fields changed in a later PDF revision' if forensic['tampered'] else 'Revision comparison unsupported; payment edits not ruled out' if forensic.get('revision_unknown') else 'No payment-field revision change found',forensic['tampered'])
    set_('C14','risk' if forensic['hidden'] else 'neutral','Hidden instruction-like text removed before AI processing' if forensic['hidden_instruction'] else 'Hidden/invisible text removed before AI processing' if forensic['hidden'] else 'No hidden text detected',forensic['hidden'])
    set_('C15','unknown' if forensic.get('revision_unknown') else 'risk' if forensic['overlay'] else 'neutral','Later text is drawn over the original bank details' if forensic['overlay'] else 'Revision comparison unsupported; overlays not ruled out' if forensic.get('revision_unknown') else 'No payment-field overlay detected',forensic['overlay'])
    set_('C17','neutral','Structured invoice extraction completed and passed schema validation',weight=0)
    inconsistent=bool(p and p.type=='BPAY' and not p.biller_code)
    set_('C18','risk' if inconsistent else 'neutral','Claims BPAY but supplies a BSB/account without a biller code' if inconsistent else 'Payment method fields are consistent')
    t=' '.join(forensic['text'].lower().split())
    bankwords=bool(re.search(r'(bank|banking) details have changed|moved banks|changed banks',t))
    set_('C19','risk' if bankwords else 'neutral','Invoice says banking details have changed' if bankwords else 'No changed-bank language detected')
    urgency=any(w in t for w in ['urgent','24 hours','do not call','immediately'])
    set_('C20','risk' if urgency else 'neutral','Urgency or pressure to pay quickly detected' if urgency else 'No urgency or pressure detected')
    directory_offer=bool(re.search(r'(domain|directory).{0,30}(renewal|listing)|not a bill',t))
    set_('C27','risk' if directory_offer else 'neutral','Directory/domain offer is presented in invoice-like language' if directory_offer else 'No disguised directory or domain-renewal offer language detected')
    relation_state,relation_evidence=relationship_state(customer,invoice)
    set_('C28',relation_state,relation_evidence)
    chronology_state,chronology_evidence=chronology(invoice)
    set_('C44',chronology_state,chronology_evidence)
    observation=SEED.get('payee_observations',{}).get(key)
    set_('C47','risk' if observation else 'neutral',observation['note'] if observation else 'No cross-customer payee reuse found in fictional bank observations',bool(observation))
    reg=abn_lookup(invoice.abn) if max_tier>=1 else None
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
        if invoice.gst>0:
            registered=reg.get('gst_registered')
            set_('C22','neutral' if registered else 'risk','Supplier is registered for GST in seeded evidence' if registered else 'Invoice charges GST but seeded registry says supplier is not GST-registered')
        else:set_('C22','unknown','Not applicable: invoice does not charge GST',applicable=False)
        registered_names=[reg['entity_name']]+reg.get('business_names',[])
        if p and p.account_name:
            payee_match=name_matches(p.account_name,registered_names)
            set_('C24','neutral' if payee_match else 'risk','Payee name matches the registered entity or business name' if payee_match else 'Payee name does not match the registered entity or business names')
            company='company' in reg.get('entity_type','').lower()
            company_marker=bool(re.search(r'\b(pty|ltd|limited|company|co)\b',p.account_name,re.I))
            personal_mismatch=company and not company_marker and not payee_match
            set_('C43','risk' if personal_mismatch else 'neutral','Personal-looking payee name conflicts with a company supplier' if personal_mismatch else 'Payee entity type is consistent with registry evidence')
        else:
            set_('C24','unknown','Payee account name unavailable for registry comparison')
            set_('C43','unknown','Payee account name unavailable for entity-type comparison')
    else:
        set_('C21','unknown','No seed registry entry; live registry not checked in replay')
        set_('C23','unknown','ABN registration age unavailable')
        set_('C22','unknown','GST registration evidence unavailable')
        set_('C24','unknown','Registered identity evidence unavailable')
        set_('C43','unknown','Registered entity-type evidence unavailable')
    domain=invoice.email.partition('@')[2]
    mismatch=bool(invoice.website and domain and domain!=invoice.website)
    free=domain in ['gmail.com','outlook.com','hotmail.com','yahoo.com']
    set_('C26','risk' if mismatch or free else 'neutral','Email differs from website or uses a free-mail provider' if mismatch or free else 'Email and website contact fields consistent')
    if max_tier>=2 and domain and not free:
        posture=dns_posture(domain)
        if posture:
            weak=not posture.get('mx') or not posture.get('spf') or not posture.get('dmarc')
            set_('C33','risk' if weak else 'neutral','Email domain lacks MX, SPF or DMARC in seeded/DNS evidence' if weak else 'Email domain has MX, SPF and DMARC evidence',weight=.2)
        else:set_('C33','unknown','Email DNS evidence unavailable')
    elif max_tier>=2:set_('C33','unknown','Not applicable: no business email domain to assess',applicable=False)
    if sup and domain:
        domain_changed=domain!=sup['known_domain']
        set_('C50','risk' if domain_changed else 'neutral',f"Invoice email domain {domain} differs from known {sup['known_domain']}" if domain_changed else 'Invoice email domain matches supplier history')
    else:set_('C50','unknown','Not applicable: no known-supplier domain comparison available',applicable=False)
    currency=foreign_currency(forensic.get('text',''))
    domestic=bool(reg and reg.get('state'))
    set_('C51','risk' if currency and domestic else 'neutral',f'Foreign currency {currency} conflicts with domestic supplier evidence' if currency and domestic else 'No foreign-currency mismatch found')
    if max_tier>=2:
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


def evidence_followup(signals,forensic):
    """Attach explanation evidence after a locked hard stop without running decision tiers."""
    by={signal['id']:signal for signal in signals}
    by['C17'].update(state='neutral',evidence='Structured invoice extraction completed and passed schema validation',weight=0,applicable=True,disposition='evidence')
    if forensic.get('original'):
        b,a=forensic['original']
        by['C39'].update(state='risk',evidence=f'Original bank details recovered from prior revision: {b} / {a}',weight=CONFIG['weights']['C39'],locked=True,applicable=True,disposition='evidence')
    else:
        by['C39'].update(state='neutral',evidence='No earlier differing payment details recovered',weight=0,applicable=True,disposition='evidence')
    return signals
