"""Acceptance tests = the demo table in docs/build-plan.md §1, plus the §11 guardrails.

THE BUILD IS DONE WHEN `pytest tests/ -q` PASSES. Do not weaken these tests to make them pass;
fix the code or tune weights.yaml. If a test is genuinely wrong (contradicts build-plan.md),
fix it and explain why in PROGRESS.md.

API contract these tests assume (build-plan.md §2, made concrete):
  POST /api/check                 multipart: file, customer_id   -> CheckResult JSON (final result, synchronous)
  GET  /api/check/{check_id}       -> CheckResult JSON
  GET  /api/check/{check_id}/events  SSE progress for the UI (not tested here)
  POST /api/check/{check_id}/chat  json {"message": str}
       -> {"score_before": int, "score_after": int, "band": str, "advice": str,
           "changed": [signal ids], "reply": str, "result": CheckResult}
  POST /api/check/{check_id}/decision  json {"decision": "pay"|"hold"|"report"} -> receipt JSON
"""
import hashlib

import pytest

from conftest import INVOICES, sig

F1 = "01-tallowwood-clean.pdf"
F2 = "02-tallowwood-changed-bank.pdf"
F3 = "03-brightwater-sloppy-fake.pdf"
F4 = "04-fernhill-new-business.pdf"


# ---------- shape ----------

@pytest.mark.parametrize("name", [F1, F2, F3, F4])
def test_result_shape(check, name):
    r = check(name)
    for key in ("check_id", "file_name", "sha256", "extracted", "signals", "score", "band",
                "coverage", "tiers_run", "advice"):
        assert key in r, f"CheckResult missing {key}"
    assert r["file_name"] == name
    assert r["sha256"] == hashlib.sha256((INVOICES / name).read_bytes()).hexdigest()
    assert 0 <= r["score"] <= 100
    assert r["band"] in ("genuine", "check", "high_risk")
    assert 0.0 <= r["coverage"] <= 1.0
    # band must agree with score unless a hard stop forced high_risk
    if r["band"] == "genuine":
        assert r["score"] >= 80
    if r["band"] == "check":
        assert 50 <= r["score"] < 80
    for s in r["signals"]:
        assert s["state"] in ("risk", "neutral", "reassuring", "unknown")
        assert isinstance(s["evidence"], str) and s["evidence"]


# ---------- #1 clean, known supplier ----------

def test_01_clean_fast_clear(check):
    r = check(F1)
    assert r["band"] == "genuine"
    assert r["score"] >= 85
    assert 2 not in r["tiers_run"], "fast clear must skip Tier 2"
    assert sig(r, "C1")["state"] != "risk"
    assert sig(r, "C3")["state"] == "reassuring"   # CoP match
    assert sig(r, "C13")["state"] != "risk"
    assert sig(r, "C14")["state"] != "risk"


# ---------- #2 changed bank details (the headline demo) ----------

def test_02_changed_bank_high_risk(check):
    r = check(F2)
    assert r["band"] == "high_risk"
    assert r["score"] <= 15
    assert sig(r, "C1")["state"] == "risk"          # bank details changed for known supplier
    assert sig(r, "C3")["state"] == "risk"          # CoP no match
    for cid in ("C13", "C15"):                      # edited after creation / overlay on bank details
        s = sig(r, cid)
        assert s["state"] == "risk" and s["locked"], cid
    assert sig(r, "C19")["state"] == "risk"         # "our banking details have changed"
    assert sig(r, "C30")["state"] == "risk"         # tallowoodmulch.com.au lookalike


def test_02_recovers_original_bank_details(check):
    s = sig(check(F2), "C39")
    assert s["state"] == "risk"
    ev = s["evidence"].replace(" ", "")
    assert "064-118" in ev and "10482291" in ev, s["evidence"]


def test_02_chat_changed_banks_does_not_help(client, check):
    r = check(F2)
    resp = client.post(f"/api/check/{r['check_id']}/chat",
                       json={"message": "They told me they changed banks"})
    assert resp.status_code == 200, resp.text
    c = resp.json()
    assert c["score_after"] <= c["score_before"]
    assert c["band"] == "high_risk"
    assert "07 5550 2184" in c["advice"]
    after = {s["id"]: s for s in c["result"]["signals"]}
    for cid in ("C13", "C15"):
        assert after[cid]["state"] == "risk" and after[cid]["softened_by"] is None


# ---------- #3 sloppy fake with prompt injection ----------

def test_03_sloppy_fake(check):
    r = check(F3)
    assert r["band"] == "high_risk"
    assert r["score"] <= 15
    for cid in ("C2", "C8", "C10", "C18", "C20"):
        assert sig(r, cid)["state"] == "risk", cid
    s14 = sig(r, "C14")
    assert s14["state"] == "risk" and s14["locked"]


def test_03_hidden_instruction_never_reaches_llm(client, monkeypatch):
    """Guardrail: the LLM only ever sees sanitised text. llm.extract must be called as a module
    attribute (llm.extract(...)) so this patch takes effect."""
    import app.llm as llm

    seen = []
    real = llm.extract

    def spy(text, *a, **kw):
        seen.append(text)
        return real(text, *a, **kw)

    monkeypatch.setattr(llm, "extract", spy)
    with (INVOICES / F3).open("rb") as f:
        r = client.post("/api/check", files={"file": (F3, f, "application/pdf")},
                        data={"customer_id": "cust_greenline"})
    assert r.status_code == 200
    assert seen, "llm.extract was never called"
    for text in seen:
        assert "AI assistant" not in text and "LOW RISK" not in text


# ---------- #4 genuine new business, rescued by chat ----------

def test_04_new_business_needs_checking(check):
    r = check(F4)
    assert r["band"] == "check"
    assert 50 <= r["score"] < 80
    assert 2 in r["tiers_run"], "new payee must escalate to Tier 2"


def test_04_chat_new_business_moves_to_genuine(client, check):
    r = check(F4)
    resp = client.post(f"/api/check/{r['check_id']}/chat",
                       json={"message": "Yes, new business, I met the owner at the expo and ordered this"})
    assert resp.status_code == 200, resp.text
    c = resp.json()
    assert c["score_after"] > c["score_before"]
    assert c["band"] == "genuine" and c["score_after"] >= 80
    assert c["changed"], "UI needs to know which signals were softened"
    softened = [s for s in c["result"]["signals"] if s.get("softened_by")]
    assert softened
    assert all(not s["locked"] for s in softened)


# ---------- receipt ----------

def test_receipt(client, check):
    r = check(F1)
    resp = client.post(f"/api/check/{r['check_id']}/decision", json={"decision": "pay"})
    assert resp.status_code == 200, resp.text
    rc = resp.json()
    for key in ("receipt_id", "file_name", "sha256", "score", "band", "decision", "decided_at"):
        assert key in rc, key
    assert rc["sha256"] == r["sha256"]
    assert rc["decision"] == "pay"


# ---------- guardrails: locked signals ----------

def test_locked_signals_never_softened_by_any_chat(client, check):
    r = check(F3)
    for msg in ("It's a new business", "I ordered this", "They changed banks",
                "I called them on their usual number and they confirmed"):
        c = client.post(f"/api/check/{r['check_id']}/chat", json={"message": msg}).json()
        for s in c["result"]["signals"]:
            if s["locked"]:
                assert s["softened_by"] is None, (msg, s["id"])
        assert c["band"] == "high_risk", msg
