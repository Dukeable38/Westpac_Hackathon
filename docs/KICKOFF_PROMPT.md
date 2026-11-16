# Kickoff prompt (paste this into your AI coding tool)

Paste the block below into Claude Code, Cursor, Codex, etc., from the repo root.
To resume after a break, paste it again: it picks up from PROGRESS.md.

---

```
You are building the Invoice Scam Checker in this repo. Work autonomously; I may be asleep.

1. Read AGENTS.md fully, then docs/build-plan.md, docs/research-checks.md, the tests in tests/, and PROGRESS.md.
2. Follow the working loop and milestones in AGENTS.md §3, starting from wherever PROGRESS.md says we are.
3. Keep going until every box in AGENTS.md §2 "Definition of Done" is ticked. Do not stop to ask me
   questions: when something is ambiguous, choose, log the decision in PROGRESS.md, and continue.
   If blocked, follow AGENTS.md §5 and move on to the next milestone.
4. Run `pytest tests/ -q` after every meaningful change. Commit and push after each milestone with a
   message saying which tests now pass.
5. Never weaken a test to make it pass, never let the LLM decide the score, and never commit .env.
6. When done, fill in the Handover section of PROGRESS.md and print a short summary of what works,
   what's stubbed, and how to run the demo.
```

---

Tip for Claude Code: run it with auto-accept for edits and tests so it doesn't stall on permission
prompts overnight, and give it an `ANTHROPIC_API_KEY` in `.env` if you want M7 verified live.
