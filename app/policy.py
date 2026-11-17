from .score import hard_stop

def decide_gate(tier,invoice,signals,supplier,score,confidence):
    by={s['id']:s for s in signals};risk={s['id'] for s in signals if s['state']=='risk'}
    if hard_stop(signals):
        return 'hard_stop','Locked high-risk evidence found in the completed tier'
    if tier==0:return 'escalate','Tier 1 common checks required'
    if tier==1:
        fast=bool(supplier and supplier['payments']['count']>=2 and by['C1']['state']=='reassuring' and by['C3']['state']=='reassuring' and invoice.total<=3*supplier['payments']['median_amount'] and not risk.intersection({'C13','C14','C15'}) and by['C21']['state']=='reassuring' and not any(s['tier']==1 and s['state']=='risk' and s['weight']>=1 for s in signals) and confidence>=.8)
        if fast:return 'fast_clear','Known stable supplier; strong checks complete with high confidence'
        return 'escalate','New, changed, uncertain or incomplete evidence requires targeted research'
    if tier==2:
        if 30<=score<=70 and invoice.total>20000:return 'escalate','High-value uncertainty requires deep checks'
        return 'budget_exhausted','Targeted checks complete; report remaining uncertainty'
    return 'budget_exhausted','Deep-check budget complete'
