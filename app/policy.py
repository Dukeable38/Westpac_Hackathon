from .score import hard_stop

def plan(invoice,signals,supplier,score,coverage):
    by={s['id']:s for s in signals}; risk={s['id'] for s in signals if s['state']=='risk'}
    fast=bool(supplier and supplier['payments']['count']>=2 and by['C1']['state']=='reassuring' and by['C3']['state']=='reassuring' and invoice.total<=3*supplier['payments']['median_amount'] and not risk.intersection({'C13','C14','C15'}) and by['C21']['state']=='reassuring' and not any(s['tier']==1 and s['state']=='risk' and s['weight']>.4 for s in signals))
    if fast: return [0,1],'Not needed: fast clear'
    reasons=[]
    if not supplier: reasons.append('new payee')
    if 'C1' in risk: reasons.append('changed bank details')
    if by['C3']['state']!='reassuring': reasons.append('payee match not confirmed')
    if 30<=score<=70: reasons.append('uncertain score')
    if any(s['tier']==1 and s['state']=='risk' and s['weight']>=1 for s in signals): reasons.append('medium or high Tier 1 flag')
    if invoice.total>5000: reasons.append('high amount')
    if coverage<.6: reasons.append('limited coverage')
    # Hard stops remain final; targeted evidence still explains the demo tampering.
    tiers=[0,1]+([2] if reasons else [])
    if 'C13' in risk or 'C15' in risk or (30<=score<=70 and invoice.total>20000): tiers.append(3)
    return tiers,', '.join(reasons) or 'Partially verified: screening budget complete'
