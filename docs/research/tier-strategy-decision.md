# Decision: use tier-gated, cost-aware checking with whole-tier gates and evidence-only follow-up after hard stops.

Decision made 17 November 2026. Policy code—not the LLM and never invoice text—controls every gate.

## Options considered

| Option | Scam coverage | False alarms | Latency/cost | Report evidence | Manipulation resistance |
|---|---|---|---|---|---|
| First red flag | Poor: a weak typo/date can hide later tampering | Worst | Lowest | Thin | Poor if attacker can manufacture an early weak flag |
| Tier-gated hard-stop | Strong: completes all checks in the current tier, then gates | Good when hard stops require precise combinations | Bounded | Strong; designated evidence checks can finish | Strong when gates use deterministic sanitized evidence |
| Run everything | Maximum available signals | Can accumulate weak noise | Worst and unpredictable | Strong | Strong, but unnecessary exposure/cost |
| Parallel all tiers with cancellation | Potentially strong | Similar to run-all | Expensive work starts before needed; cancellation unreliable | Variable | More complex than the demo needs |

The selected design is the second option with cost-aware parallelism **inside** a tier. Complete a tier rather than stopping at its first red flag. After each tier, deterministic policy returns `hard_stop`, `fast_clear`, `escalate`, or `budget_exhausted`. On a hard stop, return High/Critical promptly and mark remaining decision checks `skipped`; only explicitly named evidence checks (C17 extraction and C39 original-details recovery) may finish and must not alter the already locked level.

## Gates

- **After Tier 0:** hard stop for C13/C15 tampering, known-fraud C5, C2 register hit, government wrong account, or C1 changed details plus C3 No Match. Otherwise run Tier 1.
- **After Tier 1:** fast clear only for a known supplier with stable account, Match, amount within history, active/name-matching ABN, no Medium/High risk and confidence ≥0.80. Otherwise escalate to Tier 2 for a new payee/details, unconfirmed beneficiary, Medium/High flag, uncertain score, high amount or confidence <0.80.
- **After Tier 2:** finish if level is Low with high confidence or High/Critical; otherwise Tier 3 only for high value, conflicting strong evidence, tamper recovery, or explicit manual referral.
- **Budget exhausted:** retain current level, set unavailable applicable checks to `unknown`, report partial/low confidence, and explain what was not checked.

Hidden/invisible text is stripped before extraction. Its presence is a signal, but its content cannot decide a gate. LLM classifications feed enumerated signals only; policy owns applicability, hard stops, level and stopping.

## Worked examples

| Invoice | Expected path | Outcome/reason |
|---|---|---|
| 01 Tallowwood clean | T0 → T1 → fast clear | Known account, Match, normal amount, active/name match, no material flags: Low/high confidence. |
| 02 Tallowwood changed bank | T0 → hard stop; C17/C39 evidence only | C13/C15 tampering makes it Critical; recover original details without reopening the decision. |
| 03 Brightwater fake | complete T0 → hard stop; C17 evidence only | Register/identity/checksum evidence makes it High; hidden text cannot suppress the stop. |
| 04 Fernhill new business | T0 → T1 → T2 | Legitimate-but-new stays Medium until context explains soft history signals; never fast-clears solely from chat. |
| Nathan N1 Larana | T0 → T1 → T2 | New supplier and future-dated invoice; no hard stop, confidence partial. |
| Nathan N2 Bowing | T0 → T1 → T2 | New supplier, personal payee name and future date; gather identity evidence rather than auto-reject. |
| Nathan N3 Skype | T0 → T1 → T2 | New supplier, line-item inconsistency/future date; Medium unless stronger evidence appears. |
| Nathan N4 Fusion | T0 → T1 → T2 | Conflicting totals, customer Gmail trap and future date; do not misattribute customer contact data. |

This strategy preserves the four demo bands unless newly built evidence is deliberately seeded to change them. It also prevents a cheap weak signal from crowding out stronger evidence.
