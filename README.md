# Invoice Scam Checker

Westpac AI Hackathon (Nov 2026). A customer uploads a supplier invoice before paying it. The app runs layered checks (PDF tampering, hidden text, ABN/GST maths, changed bank details, Confirmation of Payee, lookalike domains, and more), gives a 0–100 "looks genuine" score with plain-English reasons, and lets the customer add context through chat.

**Using an AI coding tool? Start with [`AGENTS.md`](AGENTS.md).**

| Path | What it is |
|---|---|
| `docs/build-plan.md` | Build spec: architecture, scoring, checks, timeline |
| `docs/research-checks.md` | Check catalogue, escalation rules, chat rules |
| `docs/pipeline.html` | Pipeline diagram |
| `docs/team-brief.html` / `.pdf` | Team brief |
| `mockups/index.html` | Clickable front-end mock-up (open it in a browser) |
| `demo/invoices/` | 4 fictional test invoices and the script that generates them |
| `demo/seed/seed.json` | Mock bank data (customers, suppliers, CoP, flag register) |

Team: Kiel (product), Paul (build), Lauren (research and design), Nathan (pitch).
All businesses, ABNs, domains and phone numbers in this repo are fictional.
