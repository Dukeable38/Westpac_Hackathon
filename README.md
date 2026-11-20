# Radar: check an invoice before you pay it

> 🏆 **1st place, 2026 Westpac AI Hackathon (QUT Dean's Scholars)**, out of 16 teams.

Fake invoices are one of the most common scams against Australian small businesses and sole traders. A scammer edits a real invoice's bank details, or sends one that looks real enough, and the money is gone before anyone notices.

**Radar** sits inside online banking. You attach the invoice when you make a payment (or check it on its own), and Radar reads the PDF, runs a set of checks on it, and gives one of four risk levels, **Low, Medium, High or Critical**, along with the evidence behind it. If something looks off, you can explain it in a chat (for example, "it's a new business, I met the owner at an expo"), and Radar re-scores. Every decision gets a receipt that proves which invoice was checked.

This is a hackathon prototype. It uses fictional businesses only, makes no real payments, and doesn't guarantee an invoice is safe.

## What it checks

- **PDF forensics:** finds earlier revisions (for example, bank details edited after the invoice was made), overlays, hidden or invisible text, and mixed-alphabet look-alike characters.
- **Business identity:** ABN/ACN checksums, the ABN register, the GST maths, how old the domain is, and free email addresses.
- **Payment details:** whether the BSB and account match the supplier's history, BPAY consistency, and amount anomalies.
- **Pressure tactics:** urgency language, "our bank details have changed" wording, and instructions hidden from the reader.
- **Tiered checking:** cheap checks run first. A clearly tampered invoice stops early and a known, clean supplier clears fast. Only unclear invoices go on to deeper research.

There are 49 checks in the catalogue (`app/checks/catalogue.json`). Any check that isn't built yet returns `unknown` rather than guessing.

### Design rules

- **The AI never decides the score.** The model only pulls fields out of the invoice and answers narrow questions about text that our code fetched. Scores, levels and escalation are plain Python (`app/policy.py`, `app/score.py`, `app/weights.yaml`).
- **The AI never sees the raw invoice.** Hidden text is stripped out first, so instructions planted in the PDF can't reach the model.
- **Chat can't talk its way past hard evidence.** A tampered invoice stays Critical whatever the user says.
- **Radar never blocks a payment.** It warns, recommends "Report", and leaves the decision with the customer.

## Run the demo (Windows)

Needs Python 3.10 or newer. From the repo folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run_demo.bat
```

`run_demo.bat` starts the app at http://127.0.0.1:8080 in offline replay mode (recorded model answers, no API key or network needed). Then:

- **Make a payment → Attach invoice**, or **Payments → Check an invoice**, and choose a PDF from `demo/invoices/`.
- Press **Ctrl+Shift+D** to show the demo bar with one-click sample invoices.
- `/radar` shows the "Radar map": every check firing tier by tier.

On macOS or Linux, use `.venv/bin/python -m uvicorn app.main:app --port 8080` instead of the batch file.

### The demo invoices

| PDF | Result | The story |
|---|---|---|
| `01-tallowwood-clean` | 96 · **Low** | Known supplier, everything matches. Clears after the first tiers. |
| `02-tallowwood-changed-bank` | **Critical** | The bank details were edited after the invoice was made. Radar recovers the original BSB and account from the PDF's earlier revision. Saying "they told me they changed banks" doesn't help: Radar suggests calling the supplier's known number instead. |
| `03-brightwater-sloppy-fake` | **High** | Invalid ABN, wrong GST, a BPAY mismatch, urgency language and hidden instructions. |
| `04-fernhill-new-business` | 59 · **Medium** | A genuine but brand-new business. Explaining "new business, I met the owner at the expo and ordered this" moves it to 84 · **Low**. |
| `05-tallowwood-claimed-copy` | 96 · **Low** | Used with the receipt "Compare an invoice" feature: is this the same invoice I already paid? |

`demo/invoices/nathan/` holds four extra real-world-style invoices that were used to measure extraction accuracy (`scripts/extract_eval.py`), not as demo stories.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q      # 72 tests, offline
.\.venv\Scripts\python.exe scripts\smoke_demo.py    # starts a server, runs every fixture, shuts down
```

## Using a real model

By default Radar runs with `LLM_PROVIDER=fake` (deterministic regex extraction) and `DEMO_MODE=replay` (no network). To switch to a real model, copy `.env.example` to `.env`, fill in one provider block, then run `scripts\llm_smoke.py` to check it. Changing models only needs `.env`, not code.

| `LLM_PROVIDER` | Covers |
|---|---|
| `fake` | Offline and tests |
| `anthropic` | Claude, via the official SDK |
| `openai_compatible` | Anything with an OpenAI-style endpoint: OpenRouter (used for the demo), Gemini, NVIDIA NIM, Groq, local Ollama |

| `DEMO_MODE` | Behaviour |
|---|---|
| `replay` | Default. Uses answers saved in `demo/cache/`, never touches the network |
| `record` | Calls the model and saves the answers to `demo/cache/` |
| `live` | Calls the model without saving |

The demo used `nvidia/nemotron-3.5-super-vl:free` on OpenRouter. It got 78% of fields right on the extraction eval, against 32% for the regex fallback. All five demo invoices give the same results as the offline run. Never commit `.env` or API keys.

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/check` | Upload a PDF (`file`) and get the full result |
| `GET /api/check/{id}` / `.../events` | The result, or a server-sent-events replay of the tiers |
| `POST /api/check/{id}/chat` | `{"message": "..."}` gives you the re-score and what changed |
| `POST /api/check/{id}/decision` | `pay`, `hold` or `report`, and returns a receipt (SHA-256 of the invoice, never the file name) |
| `GET /api/receipts`, `POST /api/receipts/{id}/verify` | List receipts, or check a later copy of an invoice against one |

## Project layout

```
app/                FastAPI app: PDF forensics, extraction, checks, policy and scoring, chat, receipts
app/static/         The Radar UI built into a mock online-banking page (index.html, app.js, radar.css)
demo/invoices/      Fictional demo invoices and the scripts that generate them
demo/seed/          Fictional supplier history, ABN register and warning-list data
demo/cache/         Recorded model answers for offline replay
docs/               Build plan, check research, brand kit, presentation pack
collab/             How the team and our AI agents handed work to each other (task files, decisions)
mockups/            Earlier static mock-ups, kept for history
tests/              Acceptance and unit tests
```

## Limits

- Supplier history, the scam warning register and Confirmation of Payee are **mocked**. ABN, domain and web evidence for the fictional businesses comes from seed data. Nothing connects to a real bank.
- PDF forensics are heuristic. They aren't full rendering, OCR or a malware scan, and image-only invoices aren't supported.
- GST checks assume 10% on a taxable subtotal.
- There's no authentication or production hardening. Run it on localhost only.
- The mock banking screens copy the look of a real online-banking site for the demo. This project is not affiliated with or endorsed by Westpac.

## Team

Built in a week by **Kiel** (product, design and UI), **Paul** (backend and checks), **Lauren** (research and branding), **Nathan** (test invoices) and **Delvin** (the Radar name and logo animation), with AI coding agents doing a lot of the typing. `PROGRESS.md` and `collab/` keep the full build log.
