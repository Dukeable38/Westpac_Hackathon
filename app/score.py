import math
from pathlib import Path
import yaml
CONFIG=yaml.safe_load(Path(__file__).with_name('weights.yaml').read_text())

def hard_stop(signals):
    risk={s['id'] for s in signals if s['state']=='risk'}
    return bool(risk & {'C2','C13','C15','C25'}) or {'C1','C3'} <= risk or any(s['id']=='C5' and s['locked'] and s['state']=='risk' for s in signals)

def _value(signals):
    z=CONFIG['bias']+sum(s['weight'] * (-1 if s['state']=='risk' else 1 if s['state']=='reassuring' else 0) for s in signals)
    return round(100/(1+math.exp(-max(-40,min(40,z)))))

def calculate(signals):
    score=_value(signals)
    band='high_risk' if hard_stop(signals) or score<50 else 'genuine' if score>=80 else 'check'
    high=[s for s in signals if CONFIG['weights'].get(s['id'],1)>=1]
    coverage=sum(s['state']!='unknown' for s in high)/max(1,len(high))
    for s in signals:
        s['points']=score-_value([v for v in signals if v['id']!=s['id']])
    return score,band,round(coverage,3)
