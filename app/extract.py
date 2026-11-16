from . import llm
from .models import InvoiceJSON

def extract_invoice(sanitised_text):
    result=llm.extract(sanitised_text)
    return InvoiceJSON.model_validate(result)
