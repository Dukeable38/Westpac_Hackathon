from conftest import CUSTOMER, INVOICES


def upload(client, name):
    with (INVOICES / name).open("rb") as invoice:
        response = client.post(
            "/api/check",
            files={"file": (name, invoice, "application/pdf")},
            data={"customer_id": CUSTOMER},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_demo_invoices_have_four_risk_levels(client):
    expected = {
        "01-tallowwood-clean.pdf": "low",
        "02-tallowwood-changed-bank.pdf": "critical",
        "03-brightwater-sloppy-fake.pdf": "high",
        "04-fernhill-new-business.pdf": "medium",
    }

    for name, level in expected.items():
        result = upload(client, name)
        assert result["level"] == level
        assert client.get(f"/api/check/{result['check_id']}").json()["level"] == level


def test_new_business_context_moves_medium_to_low(client):
    result = upload(client, "04-fernhill-new-business.pdf")
    response = client.post(
        f"/api/check/{result['check_id']}/chat",
        json={"message": "Yes, new business, I met the owner at the expo and ordered this"},
    )
    assert response.status_code == 200, response.text
    chat = response.json()
    assert chat["level"] == "low"
    assert chat["result"]["level"] == "low"


def test_tampered_invoice_stays_critical_after_chat_and_in_receipt(client):
    result = upload(client, "02-tallowwood-changed-bank.pdf")
    response = client.post(
        f"/api/check/{result['check_id']}/chat",
        json={"message": "They told me they changed banks"},
    )
    assert response.status_code == 200, response.text
    chat = response.json()
    assert chat["level"] == "critical"
    assert chat["result"]["level"] == "critical"

    receipt = client.post(
        f"/api/check/{result['check_id']}/decision", json={"decision": "hold"}
    )
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["level"] == "critical"
