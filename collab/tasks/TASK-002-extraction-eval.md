# TASK-002 · Extraction eval on Nathan's real-style invoices

- **Status:** ready
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

## Handback
_(assignee fills in: baseline table, any real-provider tables, observations)_
