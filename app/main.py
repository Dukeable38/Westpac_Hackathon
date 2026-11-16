import copy,hashlib,uuid,json,os,asyncio,tempfile
from fastapi import FastAPI,File,Form,UploadFile,HTTPException
from .pdf_forensics import analyse
from .extract import extract_invoice
from .checks.run import evaluate
from .score import calculate
from .policy import plan
from .chat import respond
from pydantic import BaseModel,Field
from typing import Literal
from .storage import receipt
from fastapi.responses import FileResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from .seed import ROOT
(ROOT/'app/.tmp').mkdir(exist_ok=True)
tempfile.tempdir=str(ROOT/'app/.tmp')
app = FastAPI(title='Invoice Scam Checker')
RESULTS={}
app.mount('/static',StaticFiles(directory=ROOT/'app/static'),name='static')
app.mount('/demo/invoices',StaticFiles(directory=ROOT/'demo/invoices'),name='invoices')

@app.get('/')
def index():
    return FileResponse(ROOT/'app/static/index.html')

@app.post('/api/check')
async def check(file:UploadFile=File(...),customer_id:str=Form('cust_greenline')):
    try:
        data=await file.read(10*1024*1024+1)
    finally:
        await file.close()
    try:
        forensic=analyse(data)
        invoice=extract_invoice(forensic['text'])
    except Exception as exc:
        raise HTTPException(422,'Unable to read this PDF safely: '+str(exc)[:200]) from exc
    signals,sup=evaluate(invoice,forensic,customer_id)
    score,band,coverage=calculate(signals)
    tiers,reason=plan(invoice,signals,sup,score,coverage)
    for s in signals:
        if s['tier'] not in tiers:
            s.update(state='unknown',evidence='Not needed: fast clear' if tiers==[0,1] else 'Not checked within this screening',weight=0)
    score,band,coverage=calculate(signals)
    advice='Call the supplier on a number you already know before paying.' if band=='high_risk' else 'Confirm the supplier and payment details independently before paying.' if band=='check' else 'No major warning signs found. Check the details before choosing whether to pay.'
    if band=='high_risk' and sup: advice=f"Do not pay yet. Call {sup['known_phone']} (the number on your earlier invoices)."
    result=dict(check_id=uuid.uuid4().hex,file_name=file.filename,sha256=hashlib.sha256(data).hexdigest(),extracted=invoice.model_dump(),signals=signals,score=score,band=band,coverage=coverage,tiers_run=tiers,advice=advice,escalation_reason=reason,customer_id=customer_id)
    RESULTS[result['check_id']]=result
    return copy.deepcopy(result)

def get_result(check_id):
    if check_id not in RESULTS: raise HTTPException(404,'Check not found')
    return RESULTS[check_id]

@app.get('/api/check/{check_id}')
def result(check_id:str):
    return copy.deepcopy(get_result(check_id))

class Message(BaseModel):
    message:str=Field(min_length=1,max_length=2000)

@app.post('/api/check/{check_id}/chat')
def chat(check_id:str,body:Message):
    return respond(get_result(check_id),body.message)

class Decision(BaseModel):
    decision:Literal['pay','hold','report']

@app.post('/api/check/{check_id}/decision')
def decision(check_id:str,body:Decision):
    return receipt(get_result(check_id),body.decision)

@app.get('/api/check/{check_id}/events')
def events(check_id:str):
    snapshot=copy.deepcopy(get_result(check_id))
    async def stream():
        delay=min(1,max(0,float(os.getenv('DEMO_DELAY_MS','300'))/1000))
        def event(name,value):
            return f'event: {name}\ndata: {json.dumps(value)}\n\n'
        for tier in snapshot['tiers_run']:
            yield event('tier_start',{'tier':tier,'reason':snapshot['escalation_reason']})
            for signal in snapshot['signals']:
                if signal['tier']==tier:
                    yield event('signal',signal)
            if delay: await asyncio.sleep(delay)
            yield event('tier_end',{'tier':tier})
        if 2 not in snapshot['tiers_run']:
            yield event('tier_skipped',{'tier':2,'reason':'Not needed: fast clear'})
        yield event('complete',snapshot)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/health')
def health():
    return {'status':'ok'}
