# Collaboration protocol (humans + AI agents)

This folder is how the team and our AI agents hand work to each other through git.
**Any agent starting work on this repo reads this file first, then `DECISIONS.md`, then its task file.**

## Files
| Path | What it is | Who writes it |
|---|---|---|
| `collab/README.md` | This protocol | Kiel (or his agent) only |
| `collab/DECISIONS.md` | Agreed product and design decisions. **Overrides** older docs (`AGENTS.md`, `docs/build-plan.md`, `mockups/index.html`) where they conflict | Kiel (or his agent) only |
| `collab/tasks/TASK-NNN-slug.md` | One task each: goal, scope, acceptance, status | Created by Kiel's side; the assignee updates **Status** and **Log** only |
| `PROGRESS.md` | Running build log (existing) | Anyone, append-only |

## Task lifecycle
`draft` → `ready` → `claimed` → `in-review` → `done` (or `blocked`, with a reason in the Log).

- Only pick up tasks with **Status: ready** whose **Assignee** matches you (or is `any`).
- `draft` and `waiting-decision` tasks are not to be started.

## How an agent works a task
1. `git pull` the integration branch (`main` on `github.com/Dukeable38/Westpac_Hackathon`).
2. Read `collab/README.md`, `collab/DECISIONS.md`, then the task file.
3. Create a branch named **`task/TASK-NNN-slug`** from `main`.
4. Edit the task file: set `Status: claimed`, add a Log line with the date and who you are.
5. Do the work. **Stay inside the task's Scope**: don't rename, reformat or refactor files the task doesn't list. If you must touch something outside scope, say why in the Log.
6. Keep `pytest tests/ -q` green. If the task changes behaviour a test asserts, update the test in the same commit and explain why in the Log.
7. Commit messages start with the task ID:
   `TASK-003: add extraction eval script (see collab/tasks/TASK-003-extraction-eval.md)`
8. When finished: set `Status: in-review`, fill in **Handback** in the task file (what changed, how to verify, anything left), commit, and push the branch.
9. Don't merge into `main` yourself. Kiel's side reviews and merges, then sets `Status: done`.

## Where to push
- **If you can push to `Dukeable38/Westpac_Hackathon`:** push the `task/...` branch there.
- **If you can't** (Paul's cloud/tablet setup currently can't): push the same branch name to **`P00p47r00p4/Westpac_Hackathon`**. Kiel's side fetches it from there (`git fetch paul`) and merges. No access change is needed for this to work.

## Kicking off work
To hand a task to an agent, a human tells it one line:
> Pull `main` from github.com/Dukeable38/Westpac_Hackathon and follow `collab/README.md`. Your task is TASK-NNN.

Commits on `main` that open tasks use the message `collab: open TASK-NNN (see collab/tasks/...)`, so `git log --oneline` shows what's new.

## Rules that always apply
- Fictional data only. Never commit `.env`, keys, real invoices or personal data.
- The LLM never decides the score or when to stop checking. Policy code does (see `docs/research-checks.md`).
- UI/design changes need Kiel's sign-off **before** they're built. Agents may build UI only when a task says the design is approved and links the approved mock-up.
- If something in a task is ambiguous, pick the safest reading, write the assumption in the Log, and carry on. Don't block on questions.
