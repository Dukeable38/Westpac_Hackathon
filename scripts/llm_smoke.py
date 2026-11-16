"""Run the three provider operations against fictional, sanitised data."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import llm

def main():
    text='Fernhill Irrigation Co.\nABN 88 015 795 425\nAccount name Fernhill Irrigation Co Pty Ltd\nBSB 082-140\nAccount 5530 1187\nSubtotal $100.00\nGST (10%) $10.00\nTotal due (AUD) $110.00'
    invoice=llm.extract(text)
    assert invoice.abn.replace(' ','')=='88015795425'
    assert llm.classify('Does this describe a new business?',['NEW_BUSINESS','NONE'],'This is a new business')=='NEW_BUSINESS'
    assert llm.summarise('What was found?','Seeded fictional registry: Fernhill Irrigation is active.')
    print('PASS: extract, classify, summarise; provider='+llm._settings()[0])

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('FAIL: '+type(exc).__name__+': '+str(exc)[:200],file=sys.stderr);raise SystemExit(1)
