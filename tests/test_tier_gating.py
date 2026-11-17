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


def signal(result, check_id):
    return next(item for item in result["signals"] if item["id"] == check_id)


def test_clean_invoice_fast_clears_after_tier_one(client):
    result = upload(client, "01-tallowwood-clean.pdf")
    assert result["tiers_run"] == [0, 1]
    assert result["stopped_at"] == 1
    assert result["gate"] == "fast_clear"
    assert result["confidence_label"] == "high"
    assert signal(result, "C30")["disposition"] == "skipped"


def test_tampered_invoice_hard_stops_but_keeps_evidence(client):
    result = upload(client, "02-tallowwood-changed-bank.pdf")
    assert result["tiers_run"] == [0]
    assert result["stopped_at"] == 0
    assert result["gate"] == "hard_stop"
    assert result["level"] == "critical"
    assert signal(result, "C17")["disposition"] == "evidence"
    assert signal(result, "C39")["disposition"] == "evidence"
    assert "064-118" in signal(result, "C39")["evidence"]
    assert signal(result, "C18")["disposition"] == "skipped"

    chat = client.post(
        f"/api/check/{result['check_id']}/chat",
        json={"message": "They told me they changed banks"},
    ).json()["result"]
    assert chat["tiers_run"] == [0]
    assert chat["stopped_at"] == 0
    assert chat["gate"] == "hard_stop"


def test_hidden_text_cannot_prevent_tier_zero_hard_stop(client):
    result = upload(client, "03-brightwater-sloppy-fake.pdf")
    assert result["stopped_at"] == 0
    assert result["gate"] == "hard_stop"
    assert result["level"] == "high"


def test_new_business_escalates_through_tier_two(client):
    result = upload(client, "04-fernhill-new-business.pdf")
    assert result["tiers_run"] == [0, 1, 2]
    assert result["stopped_at"] == 2
    assert result["gate"] == "budget_exhausted"
    assert result["level"] == "medium"


def test_sse_exposes_gates_and_evidence_follow_up(client):
    result = upload(client, "02-tallowwood-changed-bank.pdf")
    stream = client.get(f"/api/check/{result['check_id']}/events")
    assert stream.status_code == 200
    assert "event: tier_gate" in stream.text
    assert "event: evidence_start" in stream.text
    assert "event: evidence_end" in stream.text
