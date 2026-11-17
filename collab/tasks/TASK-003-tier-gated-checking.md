# TASK-003 · Tier-gated checking with hard-stop short-circuit

- **Status:** waiting-decision (Paul's agent makes the call in TASK-004 Part A2, rewrites this spec, then sets it to `ready`)
- **Assignee:** Paul's agent
- **Branch:** `task/TASK-003-tier-gated-checking`

## Goal
Stop running deeper tiers once the decision is already made. Today the changed-bank invoice runs all four tiers even though it hit a hard stop in Tier 0.

## Scope
`app/policy.py`, `app/checks/run.py`, `app/main.py` (SSE events), `tests/`, `PROGRESS.md`.

## Spec (draft)
- Evaluate tier by tier. After each tier, a gate in `policy.py` decides `hard_stop` / `fast_clear` / `escalate` using the rules in `docs/research-checks.md`.
- On a hard stop: return the decision immediately; mark the remaining *decision* checks as `skipped` (not `unknown`). Evidence checks C17 and C39 still run and are attached to the result as `evidence`, and the SSE stream marks them "gathering evidence".
- Result gains `stopped_at` (tier number) and `gate` (`hard_stop` | `fast_clear` | `escalate_exhausted`).

## Stretch: make the event stream genuinely live
Today `GET /api/check/{id}/events` replays a check that has already finished. If time allows, emit events **as each tier actually runs** (e.g. run the check in a background task after `POST /api/check` returns the id), keeping the same event names and payloads so `/radar` and the main UI keep working. Keep the existing tests' synchronous behaviour working.

## Acceptance (draft)
- 01 stops after Tier 1 (`fast_clear`); 02 stops after Tier 0 (`hard_stop`) but still reports the recovered original details; 03 stops at the tier where its first hard stop appears; 04 escalates to Tier 2.
- All existing tests green.

## Log
- 2026-11-17 · drafted by Kiel's side; not ready until the strategy is confirmed.

## Handback
