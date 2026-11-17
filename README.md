# Invoice Scam Checker

A local, fictional-data hackathon prototype: upload an invoice PDF, inspect deterministic signals and tier progress, add context, and save a decision receipt. **It does not make payments, send fraud reports, or guarantee that an invoice is safe.** No Westpac integration or official logo is used.

## Windows quick start (PowerShell)

Install/use an existing Python **3.10 or newer**. From this repository folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe scripts\smoke_demo.py
.\.venv\Scripts\python.exe scripts\llm_smoke.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The Radar UI sits inside a mock Westpac Online Banking page (layout from `docs/westpac-reference/`). Use **Make a payment → Attach invoice** or **Payments → Check an invoice**, or click a sample invoice in the dark demo bar along the top (it runs the real checks). `/radar` is the live debug view; the previous UI is kept at `/static/classic.html`. Stop the interactive demo server with Ctrl+C. The smoke script starts a background server, tests it and always shuts it down itself. No Node build or system software is required. A `.env` file is optional: defaults are `LLM_PROVIDER=fake`, `DEMO_MODE=replay`.

Linux/macOS: use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`.

The cloud build was tested with Python 3.12; `requirements-lock.txt` records the exact installed dependency set. Windows installation/runtime itself has not been tested. `requirements.txt` is the portable supported-range installation file.

## Expected demo

| PDF | Initial result | Context |
|---|---|---|
| 01 Tallowwood clean | 96, Looks genuine | Known supplier; Tier 2 skipped |
| 02 Tallowwood changed bank | 0, High risk | Original 064-118 / 10482291 recovered; locked payment tampering and no-match |
| 03 Brightwater sloppy fake | 0, High risk | Invalid ABN, wrong GST, BPAY inconsistency, urgency and hidden instructions |
| 04 Fernhill new business | 59, Check before paying | Say “Yes, new business, I met the owner at the expo and ordered this” → 84, Looks genuine |

For #2, “They told me they changed banks” does not improve the score and recommends calling **07 5550 2184**, the prior known number. Chat cannot change locked findings. A decision is only a demo record. Receipt verification compares the local file's SHA-256, without uploading it again.

## Model configuration

Copy `.env.example` to `.env`, uncomment one provider block and restart the server. **The team is using OpenRouter** (the first block): one key gives access to many models, so comparing models is a one-line `LLM_MODEL` change. Model shortlist and eval: `collab/tasks/TASK-002-extraction-eval.md`, `TASK-004`. Never commit `.env` or real keys. Process environment variables take precedence over `.env`.

| Variable | Purpose/default |
|---|---|
| `LLM_PROVIDER` | `fake` (offline), `anthropic`, or `openai_compatible` |
| `DEMO_MODE` | `replay` default: no network; `record`: call and save evidence; `live`: call without recording |
| `DEMO_DELAY_MS` | SSE playback delay per tier; default 300, tests use 0 |
| `LLM_MODEL` | Model identifier; Anthropic default `claude-opus-5-5`; required for compatible providers |
| `ANTHROPIC_API_KEY` | Required only for Anthropic |
| `LLM_BASE_URL` | Compatible API base ending in `/v1` or provider equivalent; `/chat/completions` is appended |
| `LLM_API_KEY` | Compatible API key; local providers may accept a placeholder |
| `SEARCH_PROVIDER` | Optional `tavily`; otherwise search unavailable |
| `TAVILY_API_KEY` | Optional Tavily search key |

To test a real provider, set its key/model plus `DEMO_MODE=live` (or `record`) in `.env`, then run `scripts/llm_smoke.py`. In replay, a missing real-provider cache entry fails safely without calling the network. Both real adapters are implemented and tested with mocked transports, **not verified live**. API reference checks: [Anthropic Messages](https://platform.claude.com/docs/en/api/python/messages/create), [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).

`record` mode can save extracted fields and evidence to `demo/cache/`; use fictional data only. Review cache changes before committing. API keys and request headers are never cached. Seed-first fictional records work without network. Live ABN/domain/search adapters are best-effort, bounded, and return unknown on unavailable evidence. A live search narrative never determines the score.

## API and storage

- `POST /api/check`: multipart `file`, optional `customer_id` (default `cust_greenline`), synchronous complete result.
- `GET /api/check/{id}`: current result.
- `GET /api/check/{id}/events`: finite SSE **playback of completed checks**, including tier starts/ends, signals, skipped tiers and terminal `complete`.
- `POST /api/check/{id}/chat`: `{"message":"..."}`; returns score diff and updated result.
- `POST /api/check/{id}/decision`: `{"decision":"pay"}`, `hold` or `report`; stores receipt in ignored `app/db.sqlite`.

PDF uploads are limited to 10 MB / 20 pages. Encrypted, malformed and unsupported invisible-rendering PDFs are rejected. Multipart temporary files are confined to ignored `app/.tmp` and closed after reading. PDF bytes are not retained after processing; extracted fields/results remain in process memory until restart, and receipts persist in SQLite. No receipt deletion UI, authentication, access isolation, background worker or retention scheduler is provided. **Bind to localhost only; do not expose this prototype publicly.**

## Limits and honest coverage

- CoP, warning register, supplier history, fixture registry/domain/web data are explicitly mocked/seeded. No bank access exists. Fictional fixture ages are measured at 16 Nov 2026 for repeatable replay.
- PDF forensics are heuristic, not a full renderer/OCR or malware scanner. The supplied incremental overlay is recovered; unsupported revision layouts are unknown. Modes 3/7 are rejected; hidden small/white/off-page/zero-width text is stripped, mixed Latin/Greek/Cyrillic identifiers flagged. Complex transparency, nested forms, image-only documents and every possible malicious PDF are not comprehensively supported.
- Fake extraction is deterministic regex extraction for readable text PDFs. It is not production-grade document understanding; line items are not yet populated and GST assumes a 10% taxable subtotal. Real provider extraction validates the declared schema.
- All unimplemented checks return `unknown`; coverage is intentionally partial, not a claim of complete verification. P1/P2 IDs remain unknown unless specifically documented in `PROGRESS.md`.
- A follow-up official ABN Lookup audit found one original seed collision and replaced it: Corella now uses **93 270 000 491**. [Official lookup](https://abr.business.gov.au/ABN/View?abn=93270000491) returned no matching record. All eight checksum-valid seeded ABNs were checked and now returned no record; dated URLs/results are in `demo/seed/abn-audit.json`. This is a point-in-time check, not a permanent reservation. Domain ownership remains unverified; recheck before a public video and never use real invoices or personal data.
- The front end (`app/static/index.html`, `radar.css`, `app.js`) is the signed-off `mockups/radar/index.html` wired to the real API. It was checked in a browser on 17 Nov 2026 with all four fixtures (pay flow, standalone check, chat re-score, pay and report receipts) and two of Nathan's invoices. Bank chrome, balances and upcoming payments are fictional static demo content.

See `PROGRESS.md` for precise verification and the final handover. `mockups/` and original acceptance assertions remain unchanged.
