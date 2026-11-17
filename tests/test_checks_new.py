from app.checks.run import evaluate
from app.models import InvoiceJSON, PaymentMethod
from app.score import confidence
from app.seed import SEED


def invoice(**changes):
    data = dict(
        supplier_name="Tallowwood Mulch & Soil Co. Pty Ltd",
        abn="74284432214",
        acn="",
        email="accounts@tallowwoodmulch.com.au",
        invoice_number="INV-100",
        invoice_date="2026-11-10",
        due_date="2026-12-10",
        subtotal=100,
        gst=10,
        total=110,
        payment_methods=[
            PaymentMethod(
                type="BSB",
                bsb="064-118",
                account_number="10482291",
                account_name="Tallowwood Mulch & Soil Co Pty Ltd",
            )
        ],
    )
    data.update(changes)
    return InvoiceJSON(**data)


def forensic(text="", metadata=None):
    return dict(
        text=text,
        hidden=False,
        hidden_instruction=False,
        revision_unknown=False,
        tampered=False,
        overlay=False,
        original=None,
        metadata=metadata or {},
    )


def sig(signals, check_id):
    return next(signal for signal in signals if signal["id"] == check_id)


def run(candidate=None, evidence=None):
    return evaluate(candidate or invoice(), evidence or forensic(), "cust_greenline")[0]


def test_c9_validates_acn_checksum():
    assert sig(run(invoice(acn="123 456 780")), "C9")["state"] == "neutral"
    assert sig(run(invoice(acn="123 456 781")), "C9")["state"] == "risk"


def test_c12_flags_suspicious_pdf_editor_metadata():
    signal = sig(run(evidence=forensic(metadata={"/Producer": "iLovePDF"})), "C12")
    assert signal["state"] == "risk"


def test_c17_records_successful_structured_extraction():
    assert sig(run(), "C17")["state"] == "neutral"


def test_c22_checks_gst_registration(monkeypatch):
    monkeypatch.setitem(
        SEED["abn_registry"],
        "12345678901",
        {"status": "Active", "entity_name": "SYNTHETIC SUPPLIER", "entity_type": "Other", "gst_registered": False, "business_names": []},
    )
    candidate = invoice(supplier_name="Synthetic Supplier", abn="12345678901")
    assert sig(run(candidate), "C22")["state"] == "risk"


def test_c24_detects_unrelated_payee_name():
    candidate = invoice(payment_methods=[PaymentMethod(type="BSB", bsb="064-118", account_number="10482291", account_name="Unrelated Person")])
    assert sig(run(candidate), "C24")["state"] == "risk"


def test_c27_detects_disguised_directory_offer():
    assert sig(run(evidence=forensic("Domain renewal offer. This is not a bill.")), "C27")["state"] == "risk"


def test_c28_detects_purchase_unrelated_to_customer_industry():
    candidate = invoice(supplier_name="Bowing Aviation", abn="")
    assert sig(run(candidate), "C28")["state"] == "risk"


def test_c33_evaluates_seeded_email_dns_posture():
    candidate = invoice(email="accounts@tallowoodmulch.com.au")
    assert sig(run(candidate), "C33")["state"] == "risk"


def test_c43_detects_personal_payee_for_company_supplier():
    candidate = invoice(payment_methods=[PaymentMethod(type="BSB", bsb="064-118", account_number="10482291", account_name="Alex Example")])
    assert sig(run(candidate), "C43")["state"] == "risk"


def test_c44_detects_future_invoice_date():
    assert sig(run(invoice(invoice_date="2030-01-01")), "C44")["state"] == "risk"


def test_c47_uses_seeded_cross_customer_payee_pattern():
    candidate = invoice(
        payment_methods=[PaymentMethod(type="BSB", bsb="083-004", account_number="66201945", account_name="A Nguyen-Price")]
    )
    assert sig(run(candidate), "C47")["state"] == "risk"


def test_c50_detects_domain_change_for_known_supplier():
    assert sig(run(invoice(email="accounts@unrelated-example.test")), "C50")["state"] == "risk"


def test_c51_detects_foreign_currency_for_domestic_supplier():
    assert sig(run(evidence=forensic("Invoice total USD 110.00")), "C51")["state"] == "risk"


def test_unavailable_checks_are_honest_skeletons():
    signals = run()
    for check_id in ("C5", "C6", "C16", "C29", "C32", "C34", "C36", "C37", "C38", "C40", "C42", "C48"):
        signal = sig(signals, check_id)
        assert signal["state"] == "unknown"
        assert signal["evidence"].startswith("Not checked:")


def test_payment_specific_and_workflow_checks_can_be_not_applicable():
    signals = run()
    for check_id in ("C25", "C41", "C52"):
        signal = sig(signals, check_id)
        assert signal["state"] == "unknown"
        assert signal["applicable"] is False
        assert signal["evidence"].startswith("Not applicable:")


def test_confidence_is_weighted_applicable_evidence_coverage():
    value, label = confidence([
        {"id": "C1", "state": "neutral", "applicable": True},
        {"id": "C2", "state": "unknown", "applicable": True},
        {"id": "C17", "state": "neutral", "applicable": True},
        {"id": "C33", "state": "unknown", "applicable": False},
    ])
    assert value == 0.5
    assert label == "partial"


def test_api_results_expose_confidence(check):
    result = check("01-tallowwood-clean.pdf")
    assert 0 <= result["confidence"] <= 1
    assert result["confidence_label"] == "high"
