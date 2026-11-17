# Decisions log

Newest first. These override older docs where they conflict. Each line: date · decision · why.

## Product
- **2026-11-17 · Name is "Radar"** (no acronym). Replaces "VIP / Verified Invoice Protection", which sounded like a guarantee. Use "Radar Check", "Radar score". Never imply an invoice is verified or safe.
- **2026-11-17 · Radar is not a separate "Pay an invoice" product.** It is an action you can trigger **inside existing payment types** (Pay anyone / BSB, PayID, BPAY) by attaching an invoice. Attaching the invoice starts the whole check.
- **2026-11-17 · Also a standalone "Check an invoice" entry point** for people who aren't ready to pay. A checked invoice can later be **turned into a payment** in one step, carrying over the payee and amount.
- **2026-11-17 · Report wording depends on context.** Inside a payment flow the user hasn't paid, so don't ask "have you already paid?". The standalone checker may ask it.
- **2026-11-17 · Desktop first.** Small businesses and sole traders pay invoices from a computer (Westpac Online Banking for Business). Phone is a "nice to have".
- **2026-11-17 · Four risk levels:** Low / Medium / High / Critical (colours and copy in `docs/brand-kit.md`). Proposed mapping: **Critical** = the invoice itself was tampered with (C13, C15, C5 fraud-hash); **High** = any other hard stop (C2 register hit, C25 ATO allowlist, C1 + C3 No Match) or score < 50; **Medium** = 50–79; **Low** = ≥ 80.
- **2026-11-17 · High and Critical steer to "Report this invoice"** as the primary action. No promise that "Westpac will call you".
- **2026-11-17 · Confirmation of Payee is not our feature.** Westpac Verify already does it. Show its result as the bank's existing check; Radar adds the invoice evidence on top.

- **2026-11-17 · Real Westpac screenshots are the UI source of truth.** `docs/westpac-reference/` (Kiel's own Online Banking, redacted). Every Radar screen is built on top of these pages; where the mock-up differs, the screenshots win.
- **2026-11-17 · Delvin's opening animation is the Radar intro and loading state.** `docs/brand/radar-opening-animation.html`; `class="scanning"` on the svg loops the sonar while an invoice is being checked.
- **2026-11-17 · UI target is `mockups/radar/index.html`, signed off by Kiel and now live at `/`** (`app/static/`). Plain-English signal titles are a display layer in `app.js`; the server still decides level, score and findings. The old `mockups/index.html` is kept only as history.

- **2026-11-17 · Receipts store the invoice's SHA-256 fingerprint, never its file name** (Kiel). A file name points back to the original file on someone's computer; the hash alone proves which invoice was checked. Payments list → "Compare an invoice" checks a later copy against it (story: supplier says you still owe more).
- **2026-11-17 · Radar never blocks.** Every Medium/High/Critical result has a small "Pay anyway" link → one final warning → normal payment confirmation (Kiel).
- **2026-11-17 · Demo runs in offline replay** of recorded OpenRouter answers (`run_demo.bat`), with real drag-and-drop uploads and no demo bar (Ctrl+Shift+D shows it).

## AI
- **2026-11-17 · LLM access via OpenRouter**, through the existing `openai_compatible` provider (`LLM_BASE_URL=https://openrouter.ai/api/v1`). Model choice is open: Delvin + Paul decide using the TASK-002 eval and TASK-004 research.

## Checking strategy
- **2026-11-17 · Final call delegated to Paul's agent (TASK-004).** Kiel's side proposed: tier-gated with hard-stop short-circuit. Run a whole tier at once; after each tier a gate decides hard stop (decide High/Critical, stop deciding), fast clear (Low, stop) or escalate. Don't stop at the first red flag. After a hard stop, evidence checks (C17 extraction, C39 original-details recovery) may finish in the background for the report. Watch any invoice being checked live at `/radar`.

## Tooling
- **2026-11-17 · `/radar` is the live debug screen** (`app/static/radar.html`, `app/radar_debug.py`). It reads `app/checks/catalogue.json` at runtime, so **catalogue.json is the single source of truth for checks**: name, tier, description, executor, weight class, hard stop, built flag, and `feeds` (which checks it informs). Weights stay in `app/weights.yaml`.

## Team
- Kiel: product owner, reviews and merges. Paul: backend (+ his agent). Lauren: research and branding. Nathan: test invoices. Delvin + Paul: choosing the LLM.
