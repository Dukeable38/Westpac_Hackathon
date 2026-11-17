"""Generate 05: the invoice a supplier later claims you were sent (all businesses fictional).

Story for the receipt / hash check: Greenline paid Tallowwood INV-2041 ($3,179.00) after a Radar check.
Weeks later Tallowwood's accounts team (an honest mix-up, not a scam) says INV-2041 was really for 50 m³
of mulch and $572.00 is still owing, and sends this copy. Comparing it with the Radar receipt's fingerprint
shows it is not the invoice Greenline was sent and paid.

Usage:  python make_claimed_invoice.py   (needs Chrome or Edge + pypdf; does not touch 01-04)
"""
import shutil

from make_invoices import HERE, SRC, TALLOWWOOD, find_chrome, invoice_html, print_pdf, set_meta

CLAIMED = dict(
    TALLOWWOOD,
    title="Tallowwood INV-2041 (statement copy)",
    meta=[("Invoice no.", "INV-2041"), ("Date", "10 Nov 2026"), ("Due", "24 Nov 2026"), ("Account", "GREEN-014")],
    items=[("Premium hardwood mulch (m³)", 50, 52.00), ("Organic garden soil blend (m³)", 10, 68.00), ("Delivery, Burleigh Heads (per load)", 2, 65.00)],
    subtotal=3410.00, gst=341.00,
    note="<b>Statement reminder:</b> our records show $3,751.00 for INV-2041 and a payment of $3,179.00 received. "
         "<b>Balance outstanding: $572.00.</b> Please pay the balance within 7 days. Questions? Call 07 5550 2184.",
)


def main():
    chrome = find_chrome()
    name = "05-tallowwood-claimed-copy"
    html = SRC / f"{name}.html"
    html.write_text(invoice_html(CLAIMED), encoding="utf-8")
    raw = HERE / f"{name}.raw.pdf"
    print_pdf(chrome, html, raw)
    set_meta(raw, HERE / f"{name}.pdf", {"/Creator": "InvoiceFlow 3.2", "/Producer": "InvoiceFlow PDF engine", "/Title": "Tallowwood INV-2041"})
    raw.unlink(missing_ok=True)
    print("wrote", name)


if __name__ == "__main__":
    main()
