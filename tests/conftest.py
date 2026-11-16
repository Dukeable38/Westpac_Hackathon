"""Shared fixtures for the acceptance suite.

The suite runs fully offline: DEMO_MODE=replay (external calls served from demo/cache or seed.json)
and LLM_PROVIDER=fake (deterministic llm.py stand-in, no API key needed).
"""
import os
from pathlib import Path

import pytest

os.environ.setdefault("DEMO_MODE", "replay")
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("DEMO_DELAY_MS", "0")  # turn off the progress-animation delay in tests

ROOT = Path(__file__).resolve().parents[1]
INVOICES = ROOT / "demo" / "invoices"
CUSTOMER = "cust_greenline"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@pytest.fixture(scope="session")
def check(client):
    """check("01-tallowwood-clean.pdf") -> CheckResult dict (cached per session)."""
    cache = {}

    def _check(name: str) -> dict:
        if name not in cache:
            path = INVOICES / name
            with path.open("rb") as f:
                r = client.post(
                    "/api/check",
                    files={"file": (name, f, "application/pdf")},
                    data={"customer_id": CUSTOMER},
                )
            assert r.status_code == 200, r.text
            cache[name] = r.json()
        return cache[name]

    return _check


def sig(result: dict, check_id: str) -> dict:
    found = [s for s in result["signals"] if s["id"] == check_id]
    assert found, f"signal {check_id} missing from result (stubs must still be returned as state='unknown')"
    return found[0]
