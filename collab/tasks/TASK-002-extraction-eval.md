# TASK-002 · Extraction eval on Nathan's real-style invoices

- **Status:** in-review
- **Assignee:** Paul's agent (results go to Delvin + Paul for the model choice)
- **Branch:** `task/TASK-002-extraction-eval`

## Goal
Measure how well each candidate LLM extracts invoice fields from invoices that don't look like ours, so the team can pick a model on evidence. Today the offline `fake` extractor reads $0 and blank names on all four of Nathan's invoices.

## Scope (files you may change)
New: `scripts/extract_eval.py`, `demo/invoices/nathan/expected.json`. Edit: `README.md` (one short section), `PROGRESS.md`. **Do not** change `app/llm.py` behaviour in this task.

## Spec
1. Write `demo/invoices/nathan/expected.json`: for each of the 4 PDFs in `demo/invoices/nathan/`, the correct `InvoiceJSON` fields (see `app/models.py`). Read the PDFs yourself. Use `null` for fields not on the invoice. Notes from a first read (verify these):
   - `n1-larana-consulting.pdf`: payee account name "Larana, Inc.", BSB 063-128, account 18191550, total $95.00, no GST shown, invoice no. 000001.
   - `n2-bowing-aviation.pdf`: supplier Bowing Aviation (Daniel Loveland), **no BSB**, bank "Whelton Financial Services", account 123-456-7890, subtotal 1120, tax 112, total 1232.
   - `n3-skype-catering.pdf`: BSB 032-000, account 1212 13245, invoice INV-12345-1, subtotal shown $220.50 but line items sum to $150.50; no GST.
   - `n4-fusion-markets.pdf`: no BSB, account 123 4567 8901, subtotal 3240.00, discount 324.00, tax 291.60, total shown 2624.40 **and** "Total due $2624.00" (inconsistent). The Gmail address belongs to the *billed-to* customer, not the supplier.
2. `scripts/extract_eval.py`: runs `app.llm.extract` (via the same path the app uses: forensics text → extract) on each PDF with the provider set in `.env`, compares to `expected.json`, prints a per-field table (✓/✗) and a total accuracy %, and exits 0. Money compared to the cent; BSB/account ignoring spaces and dashes.
3. README: a 5-line "Comparing models" section showing how to run it for a provider.

## Acceptance
- `python scripts/extract_eval.py` runs with `LLM_PROVIDER=fake` (expect low accuracy; that's the baseline) and prints the table.
- If any real provider key is available, include its table in the Handback. Never commit keys.
- `pytest tests/ -q` still green.

## Log
- 2026-11-17 · opened by Kiel's side.
- 2026-11-17 · claimed by Paul's Codex agent; building the evaluator test-first on the prescribed branch.
- 2026-11-17 · evaluator and ground truth complete; fake baseline and full test suite verified on Windows.

## Handback
- Fake/replay baseline: **48/148 fields = 32.4%**. It mainly succeeds on absent fields, one shared email/website, and the Skype BSB/account; it misses line items and most identities, dates and totals.
- No real-provider table: no `.env`, `LLM_API_KEY`, or `ANTHROPIC_API_KEY` was available. No keys were created or committed.
- Ground truth captures the Fusion discrepancy (`Total Due $2624.00` versus `Total $2624.40`) and does not misattribute the billed-to Gmail address to the supplier.
- Verify with `$env:LLM_PROVIDER='fake'; $env:DEMO_MODE='replay'; .\.venv\Scripts\python.exe scripts\extract_eval.py`, then `.\.venv\Scripts\python.exe -m pytest tests\ -q`.
