# OpenRouter setup (only the steps a person does)

OpenRouter is one account and one API key that reaches models from many companies. Radar talks to it through `LLM_PROVIDER=openai_compatible`. Changing model is one line in `.env`.

## Free testing (no card needed)
1. Sign up at https://openrouter.ai (Google or email).
2. Get a key at https://openrouter.ai/settings/keys → **Create Key**. One is also created at sign-up; either works. Copy it (starts `sk-or-v1-`); it is shown only once.
3. In the project folder, copy `.env.example` to `.env`, fill in the OpenRouter block and set a free model:
   ```
   LLM_PROVIDER=openai_compatible
   LLM_BASE_URL=https://openrouter.ai/api/v1
   LLM_API_KEY=sk-or-v1-...
   LLM_MODEL=nvidia/nemotron-3.5-super-vl:free
   DEMO_MODE=record
   ```
4. Run `.venv\Scripts\python.exe scripts\llm_smoke.py`. It should print `PASS`.

Free limits: **50 requests per day** across all `:free` models (1,000/day once the account has bought at least US$10 credit). A popular free model can also be busy ("rate-limited upstream", error 429); switch `LLM_MODEL` to another `:free` model. New accounts get **no free credit**: the account starts at $0.

## Paid model for the demo (recommended)
1. https://openrouter.ai/settings/credits → **Add credits** → US$5–10 by card. Leave auto top-up off.
2. In `.env`, set `LLM_MODEL=anthropic/claude-haiku-5.5` (Paul's shortlist: `docs/research/openrouter-models.md`).
3. Run `scripts\llm_smoke.py`, then `scripts\extract_eval.py`.

## Safety
- `.env` is gitignored. Never commit it or paste the key into shared docs.
- Optional: on the key's page, set a credit limit (e.g. $5) so it can never spend more.
- After the hackathon, delete the key at https://openrouter.ai/settings/keys.

## Results so far (17 Nov 2026)
| Model | Nathan invoices (scripts/extract_eval.py) |
|---|---|
| `fake` (offline regex) | 48/148 = 32.4% |
| `nvidia/nemotron-3.5-super-vl:free` | 116/148 = **78.4%** |
| `anthropic/claude-haiku-5.5` | not yet run (needs credit) |

Demo fixtures with `nemotron-3.5-super-vl:free` (after `extract.normalise`): all four levels match the offline run (96 / 0 / 0 / 59; chat 59 → 84). About 15–20 s per check.
