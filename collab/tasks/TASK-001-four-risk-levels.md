# TASK-001 · Four risk levels in the API

- **Status:** ready
- **Assignee:** Paul's agent
- **Branch:** `task/TASK-001-four-risk-levels`

## Goal
The API returns one of four risk levels (Low / Medium / High / Critical) as well as the existing three-way `band`, so the new UI can show Lauren's four levels.

## Scope (files you may change)
`app/score.py`, `app/main.py`, `app/chat.py`, `app/storage.py`, `tests/` (new test file, plus existing tests only if they assert the changed fields), `PROGRESS.md`.

## Spec
Add `level` to every result (`POST /api/check`, `GET /api/check/{id}`, the chat response's `result`, and the stored receipt):

| level | Rule (first match wins) |
|---|---|
| `critical` | any of C13, C15, C5 is `risk` (the invoice itself was tampered with or matches a known fraud invoice) |
| `high` | any other hard stop (`hard_stop()` in `app/score.py`) **or** score < 50 |
| `medium` | 50 ≤ score < 80 |
| `low` | score ≥ 80 |

- Keep `band` exactly as it is now (backwards compatibility); `level` is additive.
- Chat can move `level` the same way it moves `band` (e.g. Fernhill medium → low), but never out of `critical` or a hard-stop `high`.

## Acceptance
- `pytest tests/ -q` green, including a new `tests/test_levels.py` asserting:
  - 01 Tallowwood clean → `low`; 02 Tallowwood changed bank → `critical`; 03 Brightwater → `high`; 04 Fernhill → `medium`, then `low` after the chat "Yes, new business, I met the owner at the expo and ordered this".
  - 02 stays `critical` after the chat "They told me they changed banks".
- `scripts/smoke_demo.py` still passes.

## Log
- 2026-11-17 · opened by Kiel's side.

## Handback
_(assignee fills in: what changed, how to verify, anything left)_
