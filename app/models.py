from typing import Literal
from pydantic import BaseModel, Field

class PaymentMethod(BaseModel):
    type: Literal['BSB', 'PAYID', 'BPAY'] = 'BSB'
    bsb: str = ''
    account_number: str = ''
    account_name: str = ''
    payid: str = ''
    biller_code: str = ''
    reference: str = ''

class InvoiceJSON(BaseModel):
    supplier_name: str = ''
    abn: str = ''
    acn: str = ''
    email: str = ''
    phone: str = ''
    website: str = ''
    invoice_number: str = ''
    invoice_date: str = ''
    due_date: str = ''
    line_items: list[dict] = Field(default_factory=list)
    subtotal: float = 0
    gst: float = 0
    total: float = 0
    payment_methods: list[PaymentMethod] = Field(default_factory=list)
    free_text_notes: list[str] = Field(default_factory=list)

class Signal(BaseModel):
    id: str
    name: str
    tier: int
    state: Literal['risk','neutral','reassuring','unknown'] = 'unknown'
    weight: float = 0
    evidence: str = 'Not checked in this demo'
    locked: bool = False
    softened_by: str | None = None
    points: int = 0
    applicable: bool = True
