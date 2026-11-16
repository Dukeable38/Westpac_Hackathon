# Instructions for AI coding agents

You are building the **Invoice Scam Checker**, a hackathon MVP for the Westpac AI Hackathon.
Demo feature freeze: **Tue 17 Nov 2026, 12:30pm AEST**. Optimise for a reliable demo, not for completeness.

## Read these first, in order
1. `docs/build-plan.md` is **the spec**. It covers architecture, data model, scoring, which checks to build, the timeline and guardrails. Follow it.
2. `docs/research-checks.md` is the check catalogue (C1–C41), tier escalation rules, and the chat `ContextClaim` enum and rule table.
3. `mockups/index.html` is **the UI target**. Lift its layout, copy and colours rather than inventing a new design. It plays all 4 scenarios (`#sc=1..4&chat=1&dec=pay` deep links).
4. `docs/pipeline.html` is the pipeline diagram (open it in a browser).

## Test fixtures (already done, don't regenerate unless asked)
- `demo/invoices/01..04-*.pdf` are the 4 demo invoices. The expected result for each is in the table in build-plan.md §1. **That table is the acceptance test.**
- `demo/seed/seed.json` holds mock customers, supplier profiles and payment history, CoP results, the flag register, ABN registry overrides and the BSB stub.
- `demo/invoices/make_invoices.py` regenerates the PDFs (needs Chrome/Edge + pypdf).

## Where to put code
Nothing is built yet. Create the app under `app/` following build-plan.md §2:
`app/main.py` (FastAPI), `pdf_forensics.py`, `extract.py`, `llm.py`, `checks/`, `policy.py`, `score.py`, `chat.py`, `sources/`, `cache.py`, `weights.yaml`.
Serve the front end from `app/static/` (start from a copy of `mockups/index.html`). Leave `mockups/` itself unchanged as the fallback for the video.

## Priority if time runs short
Fixture #2 > #4 > #3 > #1 > receipt > everything else. Build the P0 checks properly; stub the rest as `state="unknown"`.

## Non-negotiable guardrails
- The LLM never sees raw invoice text, only text that has been sanitised after hidden-text stripping (C14).
- The LLM never decides the score, the band or the escalation. Those are deterministic Python (`policy.py`, `score.py`).
- Chat can never soften a `locked` signal.
- All external calls go through `cache.py`. `DEMO_MODE=replay` must work fully offline.
- Fictional businesses only. No real Westpac logo. Don't commit API keys: use `.env` (it's gitignored).

## Run (once scaffolded)
```
python -m venv .venv && .venv\Scripts\activate      # or source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Keep `requirements.txt` and this run section up to date as you go.

## Working with the team
Kiel owns the plan and product decisions. If the spec is ambiguous, pick the option that makes the §1 demo table pass and note the assumption in your commit message. Commit small and often, and push to `main`.
