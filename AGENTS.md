# Instructions for AI coding agents

You are building the **Invoice Scam Checker**, a hackathon MVP for the Westpac AI Hackathon.
Demo feature freeze: **Tue 17 Nov 2026, 12:30pm AEST**. Optimise for a reliable demo, not for completeness.

**You are expected to work autonomously until the Definition of Done below is met.** Paul may be asleep
or away. Do not stop to ask questions. When something is ambiguous, decide, write the decision in
`PROGRESS.md`, and keep going.

---

## 1. Read these first, in order
1. `docs/build-plan.md` is **the spec**: architecture, data model, scoring, checks, guardrails. (Where it mentions "Jev" or an ABN Lookup GUID, §4 below overrides it.)
2. `docs/research-checks.md` is the check catalogue (C1–C41), tier escalation rules, and chat `ContextClaim` rules.
3. `tests/` is **the acceptance test**. The API contract is in the docstring at the top of `tests/test_acceptance.py`.
4. `mockups/index.html` is **the UI target**. Lift its layout, copy and colours. It plays all 4 scenarios (`#sc=1..4&chat=1&dec=pay`).
5. `PROGRESS.md` is the shared log. Read it at the start of every session; it says where the last session stopped.

## 2. Definition of Done (stop conditions)
You are done when **all** of these hold:
- [ ] `pytest tests/ -q` passes with no skips, running offline (`DEMO_MODE=replay`, `LLM_PROVIDER=fake`, the defaults in `tests/conftest.py`).
- [ ] `uvicorn app.main:app` serves the UI at `/`, and all 4 PDFs in `demo/invoices/` can be uploaded through the browser, showing the result, tier progress, signals, chat and receipt as in the mock-up.
- [ ] The same 4 uploads work with `LLM_PROVIDER=anthropic` (real model) if `ANTHROPIC_API_KEY` is set. If no key is available, record that in PROGRESS.md as "not verified live" (this alone doesn't block Done).
- [ ] `README.md` has accurate setup and run steps, and `requirements.txt` is complete.
- [ ] PROGRESS.md ends with a "Handover" section: what works, what's stubbed, known issues, how to run the demo.

Once all are ticked, stop adding features. Use any spare time on P1 checks (build-plan §5), but rerun the tests after each one, and never leave them red.

## 3. Working loop
Repeat until Done:
1. Read PROGRESS.md and run `pytest tests/ -q` to see what's failing.
2. Pick the next milestone below (or the next failing test inside it).
3. Implement it, run the tests, then commit and push with a message saying what now passes.
4. Append 1–3 lines to PROGRESS.md: done, decided, blocked.

Milestones, in order. Each ends with a commit.
| # | Milestone | Proof |
|---|---|---|
| M1 | Scaffold: `app/` package, FastAPI app, `requirements.txt` (include pytest + httpx), seed loader, `llm.py` with the `fake` provider | `pytest` runs and collects tests; `test_checksums.py` passes |
| M2 | PDF forensics: text, revisions, overlays, hidden text (C13, C14, C15, C39) | C13/C14/C15/C39 assertions pass |
| M3 | P0 checks + `policy.py` + `score.py` + `weights.yaml` | `test_01`, `test_02_*` (not chat), `test_03_sloppy_fake`, `test_04_new_business_needs_checking` |
| M4 | Chat (claims → rule table → re-score → diff) | all chat tests |
| M5 | Receipt + decision endpoint | `test_receipt` |
| M6 | Front end wired to the API, plus SSE progress | manual: 4 uploads in the browser look like the mock-up |
| M7 | Real LLM provider + research via web tools, cache recording | live run of the 4 fixtures; `demo/cache/` populated |

**Priority if time runs short:** fixture #2 > #4 > #3 > #1 > receipt > everything else.

## 4. LLM and research: one model, no other keys needed
- Use **one** LLM for everything: Claude via the official `anthropic` Python SDK, model **`claude-opus-5-5`**. Key in `ANTHROPIC_API_KEY` in `.env` (gitignored). Don't use Jev, and don't add a second provider.
- `llm.py` exposes these as plain module functions, called as `llm.extract(...)` (the guardrail test patches it):
  - `extract(sanitised_text) -> InvoiceJSON`: use structured outputs, validated by Pydantic.
  - `classify(question, choices, snippet) -> choice`: used for urgency, "bank details changed" language and chat claims.
  - `research(query, urls=None) -> ResearchResult`: uses the server-side tools `web_search_20260209` and `web_fetch_20260209`. Web fetch only opens URLs that appear in the conversation, so put them in the prompt, e.g. `https://abr.business.gov.au/ABN/View?abn=<digits>` for ABN status, name, GST and registration date. The result is **evidence for a check, never a score**.
- `LLM_PROVIDER=fake`: a deterministic stand-in (regex extraction, keyword classification, canned research from `seed.json`). The tests use it, and it is your fallback whenever there's no key or no network. **Build it in M1.**
- The fixture businesses are fictional, so live research on them will find nothing. Seed-first lookups (`seed.json → abn_registry`, `domains`, `web_search`) answer the fixtures; use live research only for other invoices.
- Every `research()` and live HTTP call goes through `cache.py`. `DEMO_MODE=record` saves to `demo/cache/`, and `DEMO_MODE=replay` never touches the network.

## 5. When you're blocked, don't stop
| Blocker | Do this |
|---|---|
| No `ANTHROPIC_API_KEY` | Finish everything on `LLM_PROVIDER=fake`. Mark M7 "awaiting key" in PROGRESS.md and continue. |
| No network | Same as above; replay mode and seed data cover the demo. |
| A test seems to contradict the spec | build-plan.md wins. Fix the test minimally and explain it in PROGRESS.md. Never delete assertions just to go green. |
| Can't hit a score threshold | Tune `weights.yaml` (bias and weights), not the test. |
| A check is too hard right now | Return `state="unknown"` with a reason, move on, and log it. |
| Stuck on one problem for ~30 min | Log it in PROGRESS.md under "Blocked", skip to the next milestone, and come back later. |
| A library won't install on Windows | Pick an alternative (e.g. `pypdf` + `pdfplumber` are pure Python) and log it. |

## 6. Non-negotiable guardrails
- The LLM never sees raw invoice text, only sanitised text after hidden-text stripping (C14). Research prompts contain only extracted fields (ABN, domain, names), never invoice prose.
- The LLM never decides the score, the band or the escalation. Those are deterministic Python (`policy.py`, `score.py`).
- Chat can never soften a `locked` signal.
- Fictional businesses only. No real Westpac logo. Never commit `.env` or keys.

## 7. Layout and run
Code goes in `app/`: `main.py`, `pdf_forensics.py`, `extract.py`, `llm.py`, `checks/` (incl. `identifiers.py` with `abn_valid`, `acn_valid`), `policy.py`, `score.py`, `chat.py`, `sources/`, `cache.py`, `weights.yaml`, `static/` (front end, copied from `mockups/index.html`). Leave `mockups/` unchanged as the fallback for the video.
```
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
uvicorn app.main:app --reload                        # http://127.0.0.1:8000
```

## 8. Team
Kiel owns product decisions and Paul owns the build. Commit small and often to `main`, with messages that say which tests now pass.
