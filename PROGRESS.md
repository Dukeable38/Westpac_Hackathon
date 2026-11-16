# Progress log

The AI agent appends here after each milestone or decision. Newest entries go at the bottom.
Format: `YYYY-MM-DD HH:MM · M# · done / decided / blocked: ...`

## Status
| Milestone | State |
|---|---|
| M1 Scaffold + fake LLM | not started |
| M2 PDF forensics | not started |
| M3 Checks, policy, score | not started |
| M4 Chat | not started |
| M5 Receipt | not started |
| M6 Front end + SSE | not started |
| M7 Real LLM + research + cache | not started |

## Log
- 2026-11-16 · setup · Repo, spec, fixtures, mock-up and acceptance tests in place. Nothing built yet.

## Blocked

## Handover
In progress. Final evidence follows after M7.

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
