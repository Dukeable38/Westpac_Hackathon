"""Receipts keep only the fingerprint; a later copy of an invoice can be compared against it."""
from conftest import INVOICES


def test_paid_invoice_matches_and_claimed_copy_does_not(client, check):
    r = check("01-tallowwood-clean.pdf")
    rc = client.post(f"/api/check/{r['check_id']}/decision", json={"decision": "pay"}).json()
    assert "file_name" not in rc and rc["payee"] and rc["amount"] == 3179.0
    listed = client.get("/api/receipts").json()
    assert any(x["receipt_id"] == rc["receipt_id"] for x in listed)
    assert all("file_name" not in x for x in listed)
    same = client.post(f"/api/receipts/{rc['receipt_id']}/verify",
                       files={"file": ("anything.pdf", (INVOICES / "01-tallowwood-clean.pdf").read_bytes(), "application/pdf")}).json()
    assert same["match"] is True
    other = client.post(f"/api/receipts/{rc['receipt_id']}/verify",
                        files={"file": ("x.pdf", (INVOICES / "05-tallowwood-claimed-copy.pdf").read_bytes(), "application/pdf")}).json()
    assert other["match"] is False and other["uploaded_sha256"] != other["receipt_sha256"]
