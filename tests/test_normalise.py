"""Real models copy identifiers as printed; checks must see canonical forms (found 17 Nov 2026 with OpenRouter)."""
from app.extract import normalise
from app.models import InvoiceJSON


def test_identifiers_are_canonical_whatever_the_model_returns():
    inv = normalise(InvoiceJSON.model_validate({
        "abn": "74 284 432 214", "acn": "284 432 214", "email": " Accounts@TallowwoodMulch.com.au ",
        "payment_methods": [{"type": "BSB", "bsb": "064 118", "account_number": "1048 2291", "biller_code": "48 1726"}],
    }))
    assert inv.abn == "74284432214"
    assert inv.acn == "284432214"
    assert inv.email == "accounts@tallowwoodmulch.com.au"
    p = inv.payment_methods[0]
    assert (p.bsb, p.account_number, p.biller_code) == ("064-118", "10482291", "481726")


def test_canonical_input_is_unchanged():
    inv = normalise(InvoiceJSON.model_validate({
        "abn": "74284432214", "payment_methods": [{"type": "BSB", "bsb": "064-118", "account_number": "10482291"}]}))
    assert inv.abn == "74284432214"
    assert (inv.payment_methods[0].bsb, inv.payment_methods[0].account_number) == ("064-118", "10482291")
