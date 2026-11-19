import copy
from . import llm
from .score import calculate,confidence,risk_level
from .seed import supplier,SEED

CLAIMS=['NEW_BUSINESS','SOLE_TRADER','TRADING_NAME','ORDERED_THIS','SUPPLIER_CHANGED_BANKS','VERIFIED_BY_PHONE_KNOWN_NUMBER','NONE']

def respond(result,message):
    before=result['score']; changed=[]
    claim=llm.classify('Which context claim is supported?',CLAIMS,message)
    allowed={'NEW_BUSINESS':{'C23','C31','C35'},'SOLE_TRADER':{'C26'},'ORDERED_THIS':{'C28'},'VERIFIED_BY_PHONE_KNOWN_NUMBER':{'C1'}}.get(claim,set())
    for s in result['signals']:
        if s['id'] in allowed and not s['locked'] and s['state']=='risk' and not s['softened_by']:
            s['weight']*=.5 if claim=='VERIFIED_BY_PHONE_KNOWN_NUMBER' else .3
            s['softened_by']=claim; changed.append(s['id'])
    score,band,coverage=calculate(result['signals'])
    level=risk_level(score,result['signals'])
    confidence_value,confidence_label=confidence(result['signals'])
    result.update(score=score,band=band,level=level,coverage=coverage,confidence=confidence_value,confidence_label=confidence_label)
    if claim=='SUPPLIER_CHANGED_BANKS':
        sup=supplier(result['customer_id'],result['extracted']['abn'])
        result['advice']=f"Do not pay yet. Call {sup['known_phone']} (the number on your earlier invoices)." if sup else 'Call the supplier on a number you already had, not one on this invoice.'
        if result.get('gate')!='hard_stop' and 3 not in result['tiers_run']:result['tiers_run'].append(3)
    elif changed:
        result['advice']='Your context explains some soft signals. Confirm the bank details independently before paying.'
    reply=_reply(result,claim,changed,before,score)
    return dict(score_before=before,score_after=score,band=band,level=level,advice=result['advice'],changed=changed,reply=reply,result=copy.deepcopy(result))


def _reply(result,claim,changed,before,score):
    # Conversational, invoice-specific wording. Deterministic: the LLM picks the claim, never the words of the verdict.
    ex=result['extracted'];sig={s['id']:s for s in result['signals']}
    sup=supplier(result['customer_id'],ex.get('abn',''))
    name=(sup or {}).get('name') or ex.get('supplier_name') or 'the supplier'
    short=name.split(' ')[0]
    pay=(ex.get('payment_methods') or [{}])[0]
    new_acct=f"{pay.get('bsb','')} {_a(pay.get('account_number'))}".strip()
    old=(sup or {}).get('accounts',[{}])[0]
    old_acct=f"{old.get('bsb','')} {_a(old.get('account_number'))}".strip()
    phone=(sup or {}).get('known_phone')
    locked=[s for s in result['signals'] if s['locked'] and s['state']=='risk']
    cop=sig.get('C3',{})
    held=cop.get('evidence','').split('account name ')[-1] if cop.get('state')=='risk' else ''
    if claim=='SUPPLIER_CHANGED_BANKS':
        r=f"I hear you, and that's exactly what this invoice wants you to believe. "
        if old_acct and new_acct: r+=f"You've paid {short} at {old_acct} {sup['payments']['count']} times. This invoice switches you to {new_acct}"
        else: r+=f"This invoice asks you to pay a new account ({new_acct})"
        r+=f", and that account is held by {held}, not {short}. " if held else ". "
        r+="Scammers send 'we've changed banks' notices precisely so you'll ignore a name mismatch. "
        r+=f"Call {short} on {phone}, the number on your earlier invoices, and ask them to read their BSB back to you." if phone else "Call the supplier on a number you already had, not one on this invoice."
        return r
    if claim=='VERIFIED_BY_PHONE_KNOWN_NUMBER':
        if locked: return f"Good on you for calling. But Radar found something a phone call can't fix: {locked[0]['evidence'].rstrip('.')}. Please don't pay this one until that's resolved."
        return f"That's the single best check there is. I've eased the bank-details warning. Score {before} → {score}."
    if claim=='NEW_BUSINESS':
        if changed: return f"That makes sense. A brand-new business naturally has a young website and a recent ABN, so I've eased those warnings (score {before} → {score}). Before the first payment, confirm the bank details with them by phone or in person."
    if claim=='ORDERED_THIS':
        if changed: return f"Thanks, if you placed the order, the 'did you expect this' question is answered. Score {before} → {score}."
    if claim=='SOLE_TRADER':
        if changed: return f"Sole traders often get paid into a personal account, so that's less worrying now. Score {before} → {score}."
    if locked:
        return f"Thanks for the context. It doesn't change the main problem though: {locked[0]['evidence'].rstrip('.')}. Confirmed findings like that can't be explained away in chat."
    if changed: return f"Thanks, that explains part of it. Score {before} → {score}."
    return "Thanks. That doesn't change what Radar found yet. Tell me how you know this supplier, or whether you've confirmed the bank details on a number you already had."

def _a(n):
    n=str(n or '').replace(' ','')
    return n[:4]+' '+n[4:] if len(n)==8 else n
