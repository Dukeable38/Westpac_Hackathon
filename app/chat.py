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
    reply=('Your answer softened '+', '.join(changed)+'. Locked findings were not changed.' if changed else 'Your answer does not remove the warning signs. Locked findings cannot be softened by chat.')
    return dict(score_before=before,score_after=score,band=band,level=level,advice=result['advice'],changed=changed,reply=reply,result=copy.deepcopy(result))
