import copy,hashlib,uuid,json,os,asyncio,tempfile
from fastapi import FastAPI,File,Form,UploadFile,HTTPException
from .pdf_forensics import analyse
from .extract import extract_invoice
from .checks.run import evaluate,evidence_followup
from .score import calculate,confidence,risk_level
from .policy import decide_gate
from .chat import respond
from pydantic import BaseModel,Field
from typing import Literal
from .storage import receipt,receipts,get_receipt
from fastapi.responses import FileResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from .seed import ROOT
(ROOT/'app/.tmp').mkdir(exist_ok=True)
tempfile.tempdir=str(ROOT/'app/.tmp')
app = FastAPI(title='Invoice Scam Checker')
RESULTS={}
app.mount('/static',StaticFiles(directory=ROOT/'app/static'),name='static')

@app.middleware('http')
async def no_stale_front_end(request,call_next):
    # The demo front end changes often; make browsers revalidate so a refresh always shows the latest app.js/css.
    response=await call_next(request)
    if request.url.path.startswith('/static/') or request.url.path in ('/','/radar'):
        response.headers['Cache-Control']='no-cache'
    return response
app.mount('/demo/invoices',StaticFiles(directory=ROOT/'demo/invoices'),name='invoices')
from .radar_debug import router as radar_router
app.include_router(radar_router)

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
    tiers=[];tier_gates=[];signals=sup=None
    for tier in range(4):
        signals,sup=evaluate(invoice,forensic,customer_id,max_tier=tier)
        tiers.append(tier)
        score,band,coverage=calculate(signals)
        confidence_value,confidence_label=confidence(signals)
        gate,reason=decide_gate(tier,invoice,signals,sup,score,confidence_value)
        tier_gates.append({'tier':tier,'decision':gate,'reason':reason})
        if gate!='escalate':break
    stopped_at=tiers[-1]
    if gate=='hard_stop':
        evidence_followup(signals,forensic)
        confidence_value,confidence_label=confidence(signals)
    level=risk_level(score,signals)
    advice='Call the supplier on a number you already know before paying.' if band=='high_risk' else 'Confirm the supplier and payment details independently before paying.' if band=='check' else 'No major warning signs found. Check the details before choosing whether to pay.'
    if band=='high_risk' and sup: advice=f"Do not pay yet. Call {sup['known_phone']} (the number on your earlier invoices)."
    if level=='low' and confidence_label=='low': advice='No major warning signs in the checks completed, but important checks were unavailable. Verify the details independently.'
    result=dict(check_id=uuid.uuid4().hex,file_name=file.filename,sha256=hashlib.sha256(data).hexdigest(),extracted=invoice.model_dump(),signals=signals,score=score,band=band,level=level,coverage=coverage,confidence=confidence_value,confidence_label=confidence_label,tiers_run=tiers,stopped_at=stopped_at,gate=gate,tier_gates=tier_gates,advice=advice,escalation_reason=reason,customer_id=customer_id)
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
            gate=next(item for item in snapshot['tier_gates'] if item['tier']==tier)
            yield event('tier_gate',gate)
        if 2 not in snapshot['tiers_run']:
            reason='Not needed: fast clear' if snapshot['gate']=='fast_clear' else 'Not run after '+snapshot['gate'].replace('_',' ')
            yield event('tier_skipped',{'tier':2,'reason':reason})
        evidence=[signal for signal in snapshot['signals'] if signal.get('disposition')=='evidence']
        if evidence:
            yield event('evidence_start',{'checks':[signal['id'] for signal in evidence]})
            for signal in evidence:yield event('signal',signal)
            yield event('evidence_end',{'checks':[signal['id'] for signal in evidence]})
        yield event('complete',snapshot)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/api/receipts')
def list_receipts(customer_id:str='cust_greenline'):
    """Radar receipts for the payments list (no signal detail, no file names)."""
    keep=['receipt_id','decision','decided_at','sha256','score','level','payee','amount','invoice_number','pay_to']
    return [{k:r.get(k) for k in keep} for r in receipts(customer_id)]

@app.post('/api/receipts/{receipt_id}/verify')
async def verify_receipt(receipt_id:str,file:UploadFile=File(...)):
    """Compare an uploaded PDF with the fingerprint on a receipt. The file is hashed and discarded."""
    r=get_receipt(receipt_id)
    if not r: raise HTTPException(404,'Receipt not found')
    try: data=await file.read(10*1024*1024+1)
    finally: await file.close()
    digest=hashlib.sha256(data).hexdigest()
    return {'match':digest==r['sha256'],'uploaded_sha256':digest,'receipt_sha256':r['sha256'],'receipt_id':receipt_id,
            'payee':r.get('payee'),'amount':r.get('amount'),'invoice_number':r.get('invoice_number'),'decided_at':r.get('decided_at'),'decision':r.get('decision')}

@app.get('/health')
def health():
    return {'status':'ok'}
