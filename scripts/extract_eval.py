"""Score invoice extraction against the fictional Nathan invoice ground truth."""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import llm
from app.pdf_forensics import analyse

logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)

FIXTURES = ROOT / "demo" / "invoices" / "nathan"
MONEY_FIELDS = {"subtotal", "gst", "total", "unit_price", "price", "rate"}
IDENTIFIER_FIELDS = {"bsb", "account_number"}
DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d %B %Y",
    "%B %d, %Y",
)


def flatten_fields(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        flattened: dict[str, Any] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            flattened.update(flatten_fields(child, path))
        return flattened
    if isinstance(value, list) and value:
        flattened = {}
        for index, child in enumerate(value):
            flattened.update(flatten_fields(child, f"{prefix}.{index}"))
        return flattened
    return {prefix: value}


def comparable(path: str, value: Any) -> Any:
    field = path.rsplit(".", 1)[-1]
    if value is None or value == "" or value == []:
        return None
    if field in MONEY_FIELDS:
        number = float(value)
        return None if number == 0 else round(number * 100)
    if field in IDENTIFIER_FIELDS:
        return re.sub(r"[\s-]", "", str(value)).casefold() or None
    if field in {"invoice_date", "due_date"}:
        text = str(value).strip()
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(text, date_format).date().isoformat()
            except ValueError:
                pass
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    return value


def evaluate(expected: dict[str, Any], actual: dict[str, Any]) -> list[tuple[str, bool, Any, Any]]:
    expected_fields = flatten_fields(expected)
    actual_fields = flatten_fields(actual)
    return [
        (
            field,
            comparable(field, expected_value) == comparable(field, actual_fields.get(field)),
            expected_value,
            actual_fields.get(field),
        )
        for field, expected_value in expected_fields.items()
    ]


def display(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return text if len(text) <= 42 else text[:39] + "..."


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    expected_by_file = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
    total = correct = 0
    print(f"Provider: {llm._settings()[0]} / model: {llm._settings()[1]}")
    print("invoice | field | result | expected | actual")
    print("-" * 110)
    for file_name, expected in expected_by_file.items():
        path = FIXTURES / file_name
        forensic = analyse(path.read_bytes())
        actual = llm.extract(forensic["text"]).model_dump()
        for field, matched, expected_value, actual_value in evaluate(expected, actual):
            total += 1
            correct += int(matched)
            mark = "✓" if matched else "✗"
            print(
                f"{file_name} | {field} | {mark} | "
                f"{display(expected_value)} | {display(actual_value)}"
            )
    accuracy = 100 * correct / total if total else 0
    print("-" * 110)
    print(f"Accuracy: {correct}/{total} fields = {accuracy:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
