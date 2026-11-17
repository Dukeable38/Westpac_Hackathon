import re
from . import llm
from .models import InvoiceJSON

def _digits(value):
    return re.sub(r'\D','',str(value or ''))

def normalise(invoice):
    """Put identifiers in one canonical form, whatever the model returned.

    Real models copy numbers as printed ("74 284 432 214", "1048 2291", "064 118"); the seed records and
    every check compare canonical forms. Doing this in code (not the prompt) keeps the checks deterministic.
    """
    invoice.abn=_digits(invoice.abn)
    invoice.acn=_digits(invoice.acn)
    invoice.email=str(invoice.email or '').strip().lower()
    for p in invoice.payment_methods:
        bsb=_digits(p.bsb)
        p.bsb=f'{bsb[:3]}-{bsb[3:]}' if len(bsb)==6 else str(p.bsb or '').strip()
        p.account_number=_digits(p.account_number) or str(p.account_number or '').strip()
        p.biller_code=_digits(p.biller_code) or str(p.biller_code or '').strip()
        p.payid=str(p.payid or '').strip()
    return invoice

def extract_invoice(sanitised_text):
    result=llm.extract(sanitised_text)
    return normalise(InvoiceJSON.model_validate(result))
