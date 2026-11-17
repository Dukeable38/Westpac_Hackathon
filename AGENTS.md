# Instructions for AI coding agents

> **START HERE (updated 17 Nov 2026):** read `collab/README.md` first. Work now arrives as task files in `collab/tasks/`, one branch per task. `collab/DECISIONS.md` overrides anything below that conflicts with it: the product is now **Radar**, there are **four risk levels**, and `mockups/index.html` is **no longer the UI target**. The "work autonomously until Done" loop below applies only within the scope of your assigned task.

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
- [ ] Swapping the model is `.env`-only: `fake`, `anthropic` and `openai_compatible` all implemented, `.env.example` filled in, and `python scripts/llm_smoke.py` passes for whichever real provider has a key. If no key is available, record that in PROGRESS.md as "not verified live" (this alone doesn't block Done).
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
| M7 | Real LLM adapters (`anthropic`, `openai_compatible`), code-driven research, cache recording | `scripts/llm_smoke.py` passes for any provider with a key; `demo/cache/` populated |

**Priority if time runs short:** fixture #2 > #4 > #3 > #1 > receipt > everything else.

## 4. LLM and research: plug-and-play provider
The model is **swappable by editing `.env` only**: no code changes, no restart beyond reloading. Kiel may test Claude, Gemini, NVIDIA, a free OpenRouter/Groq model, etc. on the morning of the demo. Use one model for everything (no Jev).

**`llm.py` is the only file that knows about providers.** It exposes plain module functions, called as `llm.extract(...)` (the guardrail test patches it):
- `extract(sanitised_text) -> InvoiceJSON`: ask for JSON, validate with Pydantic, retry once with the validation error on failure.
- `classify(question, choices, snippet) -> choice`: urgency, "bank details changed" language, chat claims.
- `summarise(question, page_text) -> str`: answer a question from text that **our code** fetched (used by research).

Providers, chosen by `LLM_PROVIDER`:
| `LLM_PROVIDER` | Covers | Settings |
|---|---|---|
| `fake` | Tests and offline use. Deterministic: regex extraction, keyword classification, canned research from `seed.json`. **Build it in M1.** | none |
| `anthropic` | Claude via the official `anthropic` SDK | `ANTHROPIC_API_KEY`, `LLM_MODEL` (default `claude-opus-5-5`) |
| `openai_compatible` | Anything with an OpenAI-style `/chat/completions` endpoint: **Gemini**, **NVIDIA NIM**, OpenRouter (has free models), Groq, Together, local Ollama/LM Studio | `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` |

Make `openai_compatible` work with a plain `httpx` POST (or the `openai` package), and don't depend on provider-specific features. Use JSON mode if available, otherwise "reply with JSON only" plus Pydantic validation. Free tiers rate-limit, so retry 429s with backoff and keep prompts small. `.env.example` lists ready-to-fill examples for each provider; keep it up to date.

**Research does not depend on the model having web tools.** `sources/research.py` does it in code:
1. **Fetch:** our code downloads known pages with `httpx` (e.g. `https://abr.business.gov.au/ABN/View?abn=<digits>` for ABN status, name, GST and registration date; crt.sh; Wayback CDX; DNS over HTTPS). No API key is needed.
2. **Search (optional):** if `SEARCH_PROVIDER=tavily` and `TAVILY_API_KEY` are set, use Tavily (free tier). Otherwise web-search checks return `unknown` ("search not configured"). Don't fail.
3. **Read:** pass the fetched text plus a narrow question to `llm.summarise()`. Parse simple facts (dates, status) with code where possible.

The result is **evidence for a check, never a score**. With `LLM_PROVIDER=anthropic`, you *may* also use its server-side `web_search_20260209` / `web_fetch_20260209` tools as an upgrade, but the code path above must work with every provider.

- The fixture businesses are fictional, so live research on them will find nothing. Seed-first lookups (`seed.json → abn_registry`, `domains`, `web_search`) answer the fixtures; live research is only for other invoices.
- Every LLM, research and HTTP call goes through `cache.py`, keyed by (provider, model, input). `DEMO_MODE=record` saves to `demo/cache/`, and `DEMO_MODE=replay` never touches the network.
- Add `scripts/llm_smoke.py`: it runs `extract` + `classify` + `summarise` once against the configured provider and prints pass/fail. It's the 30-second check after swapping keys.

## 5. When you're blocked, don't stop
| Blocker | Do this |
|---|---|
| No API key for any provider | Finish everything on `LLM_PROVIDER=fake`, and still write the `anthropic` and `openai_compatible` adapters so a key just plugs in. Mark M7 "awaiting key" in PROGRESS.md and continue. |
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
