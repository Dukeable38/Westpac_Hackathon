# TASK-003 · Tier-gated checking with hard-stop short-circuit

- **Status:** in-review
- **Assignee:** Paul's agent
- **Branch:** `task/TASK-003-tier-gated-checking`

## Goal
Stop running deeper tiers once the decision is already made. Today the changed-bank invoice runs all four tiers even though it hit a hard stop in Tier 0.

## Scope
`app/policy.py`, `app/checks/run.py`, `app/main.py` (SSE events), `tests/`, `PROGRESS.md`.

## Spec (approved by TASK-004 Part A2)
- Implement `docs/research/tier-strategy-decision.md`: cost-aware parallelism may occur inside a tier, but complete the tier before its deterministic gate.
- The gate in `policy.py` returns `hard_stop`, `fast_clear`, `escalate`, or `budget_exhausted`; the LLM never chooses a gate.
- After Tier 0, hard-stop on C13/C15 tampering, known-fraud C5, C2, C25, or C1 + C3 No Match. Otherwise run Tier 1.
- After Tier 1, fast-clear only for a known stable supplier with Match, normal amount, active/name-matching ABN, no Medium/High risk, and confidence ≥0.80. Escalate for new/changed payees, unconfirmed beneficiary, Medium/High risk, uncertain score/high amount, or confidence <0.80.
- After Tier 2, finish Low only with high confidence; use Tier 3 only for high value, conflicting strong evidence, tamper recovery or manual referral.
- On hard stop, lock the result immediately; mark remaining applicable decision checks `skipped`. C17 and C39 may finish as `evidence` but cannot change the locked level.
- Result gains `stopped_at`, `gate`, `confidence`, and `confidence_label`. Signals distinguish `skipped`, `not_applicable`, and `unknown` so confidence is honest.

## Stretch: make the event stream genuinely live
Today `GET /api/check/{id}/events` replays a check that has already finished. If time allows, emit events **as each tier actually runs** (e.g. run the check in a background task after `POST /api/check` returns the id), keeping the same event names and payloads so `/radar` and the main UI keep working. Keep the existing tests' synchronous behaviour working.

## Acceptance
- 01 stops after Tier 1 (`fast_clear`) with high confidence.
- 02 stops after Tier 0 (`hard_stop`) but still reports recovered original details as evidence; chat cannot reopen it.
- 03 stops after the complete tier containing its first hard stop; hidden text cannot control the gate.
- 04 escalates to Tier 2 and does not fast-clear merely because chat explains new-business signals.
- Applicable unavailable checks lower confidence; `not_applicable` checks do not. A Low result with low confidence uses qualified advice.
- SSE exposes tier gates, skipped decision checks and evidence follow-up while preserving existing synchronous API tests.
- All existing tests green.

## Log
- 2026-11-17 · drafted by Kiel's side; not ready until the strategy is confirmed.
- 2026-11-17 · rewritten and set ready by TASK-004 Part A2; decision: tier-gated, cost-aware whole-tier gates with evidence-only follow-up after hard stops.
- 2026-11-17 · claimed by Paul's Codex agent; implementing deterministic gates test-first on the prescribed branch.
- 2026-11-17 · implementation complete; hard-stop chat regression fixed and full suite/smoke verified on Windows. Ready for review.
- 2026-11-17 · scope note: touched `app/models.py` to represent signal disposition and `app/chat.py` so chat cannot append Tier 3 to a locked hard stop; both are required by this task's acceptance rules.

## Handback
- Implemented deterministic whole-tier gates in `policy.py` and bounded evaluation through the current tier.
- 01 runs T0/T1 then `fast_clear`; 02 and 03 stop after T0 `hard_stop`; 04 runs through T2 then `budget_exhausted`.
- Hard stops run only C17/C39 as `evidence`; later decision checks are `skipped`. Chat cannot reopen a locked hard stop.
- Results expose `stopped_at`, `gate`, `tier_gates`, confidence, and per-signal `disposition`; SSE adds `tier_gate` and evidence lifecycle events.
- Updated two older acceptance assertions that previously required T1/T2 checks after a T0 hard stop; risk levels, scores and locked evidence remain unchanged.
- Verify with `.\.venv\Scripts\python.exe -m pytest tests\ -q` and `.\.venv\Scripts\python.exe scripts\smoke_demo.py`.
