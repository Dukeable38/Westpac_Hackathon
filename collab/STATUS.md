# Status (where things stand)

> **Final status (20 Nov 2026): the hackathon is over and Radar won 1st place out of 16 teams.** The project is finished and archived; there is no work in flight. The notes below are the 17 Nov snapshot, kept for history. See the top-level `README.md` for how to run it.

Snapshot for anyone (human or agent) picking up the work. Last update before the final: **17 Nov 2026, ~12:40 AEDT**.

**Hard deadline: demo video due 4:00pm 17 Nov.** Shortlist presentation Friday.

## Working
- Backend (Paul): FastAPI app, 21 of 41 checks built, scoring, tier escalation, chat, receipts. **TASK-001 merged** (API returns `level`: low/medium/high/critical). `pytest tests/ -q` = 45 passing. Runs on Windows (see README).
- `/radar`: live sonar-style debug screen. Reads `app/checks/catalogue.json` at runtime; follows checks started in the app ("Follow app"). Today it replays each finished check at a readable pace; truly live streaming is TASK-003's stretch goal.
- `mockups/radar/index.html`: **current UI mock-up**, rebuilt on Kiel's real Westpac screenshots (`docs/westpac-reference/`, the UI source of truth) with Delvin's logo animation as the loading state. Kiel: OK as of 17 Nov. Covers: Radar as "Attach invoice" inside Make a payment; standalone "Check an invoice" with "Pay this invoice"; 4 risk levels; Report first for High/Critical; context-aware Report wording; Westpac Verify shown as the bank's existing check. Not wired to the backend. Awaiting Kiel's sign-off.
- Brand: `docs/brand-kit.md`, logo previews in `docs/brand/` (leaning v5).

- **Main app UI = Radar** (`/`): the mock-up wired to the real API. Sample invoices in the demo bar run real checks. Old UI at `/static/classic.html`.

## In flight (Paul's agent, see `collab/tasks/`)
- TASK-004: signal research, **final call on the checking strategy**, OpenRouter model shortlist, building checks (full or skeleton), confidence measure.
- TASK-002: extraction scorecard on Nathan's invoices (model choice).
- TASK-003: tier-gated checking; spec rewritten by TASK-004 Part A2.
Merge their `task/*` branches after review; they may arrive on `origin` or on Paul's repo (`git fetch paul`).

## Not started / next
- ~~Before the repo goes public: delete or redact `docs/westpac-reference/01-overview-dashboard.png`.~~ Done (removed 17 Nov).
- Unmerged: `paul/invoice-scam-checker` eb5e975 (LLM timeout + Retry-After backoff). Review and merge if useful.
- Real LLM: put an OpenRouter key in `.env` (never commit), pick a model from TASK-002/004, run `scripts/llm_smoke.py` and the 4 Nathan invoices.
- Lauren: tone of voice, final logo colour, clean logo exports.
- Pitch stats: verify the $2.0M small-business figure and the "<10% reimbursement" claim before they go in the deck (see chat notes; `docs/research-checks.md` has sourced stats).

## How to run
`python -m venv .venv` → `.venv\Scripts\python.exe -m pip install -r requirements.txt` → `.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`. App at `/`, live debug at `/radar`. Open the mock-up straight from disk.
