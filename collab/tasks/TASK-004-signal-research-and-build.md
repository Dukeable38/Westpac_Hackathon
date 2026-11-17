# TASK-004 · Signal research, tier strategy call, and building the checks

- **Status:** claimed
- **Assignee:** Paul's agent
- **Branches:** `task/TASK-004a-research` (docs only), then `task/TASK-004b-build` (code)
- **Hard deadline for anything that should appear in the video:** merged by **3:00pm AEDT 17 Nov** (video due 4pm). Work after that is for the Friday shortlist presentation.

## Why
Radar's value is the breadth and quality of its checks. Today 21 of 41 catalogued checks are built; the rest return `unknown`. Kiel wants you to (1) research what we should check for, (2) make the final call on how checks escalate, and (3) **build** the checks, as skeletons where the full version isn't feasible today, so the score and its confidence reflect what was actually checked.

## Read first
1. `collab/README.md`, `collab/DECISIONS.md`
2. `app/checks/catalogue.json` (single source of truth: every check's name, tier, description, executor, weight class, hard stop, `built` flag, `feeds`)
3. `docs/research-checks.md` (original research: tiers, escalation rules, chat rules, data sources, stats)
4. `app/checks/run.py`, `app/policy.py`, `app/score.py`, `app/weights.yaml`, `app/pdf_forensics.py`, `app/sources/research.py`
5. Run the app and open **`/radar`**: the live debug screen. Upload invoices (buttons 01–04, N1–N4) and watch which checks fire. Your new checks appear there automatically once they're in `catalogue.json`.

---

## Part A · Research (docs only, can start immediately, parallel with everything)
Write `docs/research/signals-review.md`. Use web research; cite sources (URL + date) for every factual claim. Australian context first.

1. **Gap analysis: what should Radar check that it doesn't?** Think like a fraud analyst at an Australian bank and like a scammer. Seeds to consider (not exhaustive, reject what doesn't hold up):
   - PayID name vs invoice supplier; BPAY biller code validity and biller name vs supplier; BPAY CRN check digit
   - QR codes or payment links inside the PDF pointing somewhere other than the stated bank details
   - Invoice number sequence and cadence vs this supplier's history; amount just under approval limits; round-number amounts
   - Document producer (e.g. Canva/Word/online PDF editor) vs what this supplier normally sends
   - Account name looks like a person when the supplier is a company (and vice versa)
   - Recently changed supplier email domain; reply-to/sender mismatch (if the invoice arrived by forwarded email)
   - Cross-customer signals: the same new account appearing on invoices for many unrelated suppliers (mule pattern); same invoice template reused across "different" suppliers
   - Invoice dated in the future or far past; due date pressure; foreign currency on a domestic supplier
   - Anything from ACCC/Scamwatch/NASC, ASD/ACSC, AFP, AusPayNet, AFCX or bank publications on BEC/payment-redirection red flags
2. **Changes to existing checks:** wrong tier? wrong weight class? should be / shouldn't be a hard stop? redundant with Westpac Verify (CoP)? Explain each.
3. **For every proposed check** (new or changed), one table row: ID (new ones continue from C42), name, one-sentence plain-English description (same style as `catalogue.json`), tier, executor (code / LLM / external API / mock), data source, weight class, hard stop?, chat-adjustable?, `feeds`, effort (S/M/L), and **demo-able today with fictional data?** (y/n).
4. **Prioritised shortlist:** the top 5–8 to build first, by (fraud-catching value × demo visibility) ÷ effort.

## Part A2 · Final call on the checking strategy (docs only)
Kiel has delegated this decision to you. Write `docs/research/tier-strategy-decision.md`:
- Options: (a) stop at the first red flag, (b) tier-gated with hard-stop short-circuit (Kiel's side's proposal), (c) run everything, (d) anything better you find (e.g. cost-aware ordering within a tier, parallel tiers with early cancel).
- Evaluate against: catching scams, false alarms on genuine-but-new suppliers (Fernhill), latency/cost per invoice, evidence for the report, and resistance to manipulation (the invoice is attacker-controlled; hidden text must not influence when checking stops).
- Use the 4 demo invoices + Nathan's 4 as worked examples.
- **State the decision in one line at the top.** Then rewrite `collab/tasks/TASK-003-tier-gated-checking.md` to match your decision and set its Status to `ready`. Kiel's merge of your branch is the approval.

## Part A3 · OpenRouter model shortlist (docs only)
Write `docs/research/openrouter-models.md`: 3–5 OpenRouter models suited to (1) structured extraction from invoice text to strict JSON, (2) short yes/no classification, (3) reading a page of search results. For each: id, price per 1M tokens in/out, context length, JSON-mode / structured-output support, vision support (for image-only PDFs), typical latency, free-tier limits. Recommend one default and one cheap fallback. Feed the ids into TASK-002's eval if a key is available.

---

## Part B · Build the checks (code, after Part A; branch from `main` after TASK-001 is merged if possible)
For every check in your shortlist, **and** for every currently unbuilt check in `catalogue.json` (`"built": false`):
- Implement it in `app/checks/` (new module per group is fine, e.g. `app/checks/payment.py`, `app/checks/document.py`). Wire it into `evaluate()` in `run.py`.
- **Full implementation** where feasible with fictional/seeded data. Add seed data to `demo/seed/seed.json` as needed (fictional only).
- **Skeleton** where it isn't: the function exists, has a docstring explaining the real implementation and data source, and returns `unknown` with evidence like `"Not checked: needs <data source>"`. Mark these `"built": "skeleton"` in `catalogue.json` (the debug screen treats anything not `true` as not fully built).
- Add each new check to `catalogue.json` with all fields (match the existing format exactly) and its weight to `weights.yaml`.
- One test per fully built check in `tests/test_checks_new.py`, using the demo invoices or small synthetic inputs.

## Part C · Confidence, not just score
With many checks returning `unknown`, a high score can hide a thin check. Design and implement a **confidence** measure alongside the score:
- Weight coverage by importance: share of the *applicable* high-weight checks that returned real evidence (`risk`/`neutral`/`reassuring`). Skeletons and "not applicable" (e.g. BPAY checks on a BSB invoice) must be handled explicitly; don't let N/A count against confidence.
- Add `confidence` (0–1) and `confidence_label` (`high` / `partial` / `low`) to results. Rule of thumb to start from: a **Low risk** result with **low confidence** must not read as "Looks good"; the advice should say what couldn't be checked.
- Explain the formula in `docs/research/signals-review.md` and test it.

## Constraints
- Keep `pytest tests/ -q` green on every commit. Existing acceptance results for the 4 demo invoices must not change band unless your Part A2 decision requires it; if so, say so explicitly in the Handback.
- The LLM never sets the score, the level or when to stop. Policy code does.
- Never commit `.env`, keys, real invoices or personal data.
- Don't edit UI files (`app/static/index.html`, `app/static/app.js`, `mockups/`). `/radar` will pick up your catalogue changes by itself.

## Handback (fill in when done)
- Decision (A2) in one line:
- Checks added / changed (IDs), and which are full vs skeleton:
- Confidence formula and example values for the 8 invoices:
- How to verify (commands, which invoices to drop into `/radar`):
- Open questions for Kiel:

## Log
- 2026-11-17 · opened by Kiel's side.
- 2026-11-17 · claimed by Paul's Codex agent; Part A research and strategy decision started on `task/TASK-004a-research`.
- 2026-11-17 · Parts A/A2/A3 complete on research branch: sourced signal review, tier decision, TASK-003 rewrite, and four-model OpenRouter shortlist. Part B/C remains in progress.
