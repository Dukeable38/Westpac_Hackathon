"""Small unit tests for deterministic checks. Expected module: app/checks/identifiers.py
exposing abn_valid(str) -> bool and acn_valid(str) -> bool (spaces allowed in input)."""
import json

import pytest

from conftest import ROOT


def test_seed_abns_are_valid():
    from app.checks.identifiers import abn_valid

    seed = json.loads((ROOT / "demo" / "seed" / "seed.json").read_text(encoding="utf-8"))
    for sup in seed["customers"][0]["suppliers"]:
        assert abn_valid(sup["abn"]), sup["name"]


@pytest.mark.parametrize("abn", ["51 824 753 556", "51824753556"])  # the ATO's published example ABN
def test_abn_valid_examples(abn):
    from app.checks.identifiers import abn_valid
    assert abn_valid(abn)


@pytest.mark.parametrize("abn", ["12 345 678 901", "74284432215", "123"])
def test_abn_invalid_examples(abn):
    from app.checks.identifiers import abn_valid
    assert not abn_valid(abn)
