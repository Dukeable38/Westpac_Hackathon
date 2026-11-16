from app.checks.run import evaluate
from app.models import InvoiceJSON,PaymentMethod

def fixture_invoice():
    return InvoiceJSON(supplier_name='Tallowwood Mulch & Soil Co Pty Ltd',abn='74284432214',total=10000,subtotal=9090.91,gst=909.09,email='accounts@tallowwoodmulch.com.au',website='tallowwoodmulch.com.au',payment_methods=[PaymentMethod(bsb='064-118',account_number='10482291')])

def forensics():
    return dict(text='',hidden=False,hidden_instruction=False,tampered=False,overlay=False,original=None,metadata={})

def test_amount_anomaly():
    signals,_=evaluate(fixture_invoice(),forensics(),'cust_greenline')
    assert next(s for s in signals if s['id']=='C7')['state']=='risk'
