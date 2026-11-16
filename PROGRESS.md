# Progress log

The AI agent appends here after each milestone or decision. Newest entries go at the bottom.
Format: `YYYY-MM-DD HH:MM · M# · done / decided / blocked: ...`

## Status
| Milestone | State |
|---|---|
| M1 Scaffold + fake LLM | complete |
| M2 PDF forensics | complete |
| M3 Checks, policy, score | complete |
| M4 Chat | complete |
| M5 Receipt | complete |
| M6 Front end + SSE | complete |
| M7 Real LLM + research + cache | complete; real-provider live verification unavailable for M7 |

## Log
- 2026-11-16 · setup · Repo, spec, fixtures, mock-up and acceptance tests in place. Nothing built yet.

## Blocked



## Build log
- 2026-11-16 · M1 · Scaffold, local .venv, seed loader and fake extraction: checksum tests passed (6); acceptance collected.
- 2026-11-16 · M2 · Revision/overlay detection and recovery, hidden-text sanitisation implemented from PDF evidence, not filenames.
- 2026-11-16 · M3 · P0 checks, deterministic weights and tiers implemented: all non-chat/non-receipt acceptance passed.
- 2026-11-16 · M4 · Fixed claim table, score diff and locked-signal protection: chat acceptance passed.
- 2026-11-16 · M5 · SQLite receipt storage added; all 20 original tests pass, zero skips.
- Decision: upstream AGENTS.md has sections 1–8 only; requested section 9 is absent. Full source read.
- Decision: initial M1–M4 commits delayed to honour the stronger “never leave tests red at a commit” rule; all milestone commits below use the first fully green integrated state. Upstream snapshot 6236d8d imported through authenticated GitHub connector; later user direction authorises publication to a separate branch, never main.
- 2026-11-16 · M6 · SSE event playback and bounded smoke script implemented. Script starts/stops its own uvicorn; UI, four uploads (96/0/0/59), complete SSE, chat and receipt pass. Local HTTP uses trust_env=False to avoid inherited proxy settings.
- 2026-11-16 · M7 · fake/anthropic/openai_compatible adapters, validated JSON extraction/retry, bounded 429 retries, seed-first code research and record/replay cache complete. Fake LLM smoke passed; real providers not verified live (no key). Mocked transport tests cover both real adapters without network.
- Decision: research missing/failed evidence remains unknown; ABN dates/GST and live search counts are not inferred from LLM prose. SSE is a replay of completed synchronous checks (API contract), not a live in-flight job. Coverage includes unimplemented high-weight checks and is intentionally partial.
- Review fixes: fast-clear now gates Tier 2 research before calls; regression proves no domain/search calls. Invisible PDF text rendering modes 3/7 rejected before any LLM call; mixed-script identifiers stripped/flagged; unsupported revision comparisons marked unknown. Multipart temporary files stay inside repo and uploads are explicitly closed; PDFs not retained. 35 tests pass, zero skips.

## Definition of Done evidence
1. PASS: `pytest tests/ -q`: **35 passed, 0 failed, 0 skipped**, including all 20 original tests unchanged. Defaults: replay/fake. Additional tests cover locked weights, renamed PDFs, invalid inputs, fast-clear gating, invisible rendering rejection, provider mocks and no-network replay.
2. PASS: `scripts/smoke_demo.py` starts a background uvicorn on an ephemeral local port, waits ≤10 s, checks HTML, all four PDFs (96 genuine / 0 high_risk / 0 high_risk / 59 check), finite SSE completion, chat → 84 genuine and receipt; shuts down in finally. Exit 0.
3. PASS: frontend in app/static retains mock-up CSS/layout and uses API upload, signal/tier SSE playback, chat/diff and decisions/receipts. JavaScript syntax check exit 0. mockups unchanged. No visual-browser QA claimed (scripted replacement requested).
4. PASS: fake, anthropic and openai_compatible implemented in app/llm.py; .env selection. `scripts/llm_smoke.py` fake pass; both real adapters tested with mocked transports. Real providers **not verified live**, no keys provided or used.
5. PASS: requirements.txt includes runtime/test dependencies, requirements-lock.txt records tested cloud versions; `pip check` reports no broken requirements. README contains Windows setup/run/provider steps.
6. PASS at final commit: no .env or real key tracked; work committed locally. Latest user authorisation supersedes original no-push: also publish to **invoice-scam-checker**, not main, using GitHub connector. Source and mockups preserved.
7. PASS: handover below includes works/stubs/known issues/decisions/unverified and exact commands.

## Handover
### What works
All four supplied PDFs produce the expected bands offline. Prior payment fields are recovered from the actual PDF revision, not filenames. Hidden instructions are excluded before llm.extract; invisible Tr=3/7 inputs are rejected. Locked signals cannot be softened. New-business context moves 59 → 84. Real API frontend, finite SSE playback, SQLite receipts and local SHA-256 verification work. All 35 tests and two smoke scripts pass.

### Stubbed / deliberately limited
CoP, supplier history and warning register are mocked. Fixture ABN/domain/web evidence is seeded. P1/P2 checks not implemented return unknown with reasons: C5, C6, C7, C9, C11, C12, C16, C17, C22, C24, C25, C27, C28, C29, C32, C33, C34, C36, C37, C38, C40, C41. C35 seeded web evidence is implemented because new-business chat needs it; unsupported live search counts stay unknown. No payment, report, reminder or bank integration occurs. Fake extraction does not populate line items. Chat explanatory reply is a deterministic statement of the applied diff, not unconstrained generated advice.

### Known issues / decisions
Heuristic PDF inspection is not full OCR/render validation; complex transparency, forms and unsupported revisions require manual review. GST assumes 10% taxable subtotal. Replay fixture age uses 16 Nov 2026. Coverage is intentionally partial and displayed; a green band is not proof of safety. SSE plays the synchronous API's completed evidence, not a live background job. Results are in memory; receipts persist in ignored SQLite. No authentication, public hosting, retention UI, or production hardening. Use fictional invoices and localhost only. User's latest branch-publication direction supersedes the earlier local-only clause. Milestone commits M1–M5 were combined to obey the stronger no-red-commit rule; intermediate failing progress was logged, assertions not weakened.

### Not verified
Anthropic/OpenAI-compatible live calls (no key); live ABN/crt.sh/Wayback/DNS/Tavily reachability and correctness; Windows installation/runtime; visual browser interaction/accessibility; whether invented ABNs/domains remain unassigned; performance under concurrent load. Provider mocks are not live-provider evidence. No claim that public hosting exists.

### Exact demo commands (PowerShell, repository root)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe scripts\smoke_demo.py
.\.venv\Scripts\python.exe scripts\llm_smoke.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000. Default fake/replay needs no key. For cloud/Linux replace the executable with `.venv/bin/python`. The smoke server is automatically stopped. All implementation work took place in the cloud, not the user's Windows clone.
