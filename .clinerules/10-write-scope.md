# Write-Scope Rule (read this before your first edit)

Two agents share this repo. To stop us overwriting each other's work, write access is
partitioned by backend section. **Read access is never restricted.**

## Rule 0 — Declare your section before editing

Start every task by stating your section and its scope path, e.g.
`Working in section: card_storage (scope: backend/app/sections/card_storage/)`.
If the task does not name a section, ask which one before touching any file.

## Rule 1 — Write only inside your assigned section

Your write scope is exactly:

- `backend/app/sections/<your_section>/` (all files and subfolders, e.g. `prompts/`)
- `backend/tests/sections/test_<your_section>.py`

Do not create, edit, move, rename or delete anything outside that scope.

## Rule 2 — Everything else is read-only

You may read the whole repo — `app/core/`, `app/main.py`, other sections, `frontend/`,
docs, configs — to understand contracts and conventions. Reading is never a violation.
Writing is.

## Rule 3 — Ask before you cross the line

If a task genuinely needs a change outside your scope, **stop and ask first**. Your
request must include:

1. The exact file(s) you want to change.
2. The precise change.
3. Why your section cannot solve it alone.
4. The smallest alternative, if one exists.

Then wait for an explicit yes. Permission is for that file and that task only — it does
not carry over to later tasks or to other files.

Common cases that need permission: adding a route to `app/main.py`, changing
`app/core/config.py` or `app/core/database.py`, adding a dependency to
`requirements*.txt`, editing another section, touching `.clinerules/`.

## Rule 4 — Shared / lead-owned files

These are owned by the project lead; treat them as read-only unless the current task is
an explicit setup, integration, dependency or refactor task from the lead:

`backend/app/main.py`, `backend/app/core/**`, `backend/app/sections/__init__.py`,
`backend/requirements*.txt`, `backend/requirements-dev.txt`, `backend/pyproject.toml`,
`backend/.env.example`, `backend/tests/conftest.py`, `README.md`/`*.md` at the repo
root, `.gitignore`, `.clinerules/**`, `frontend/**`.

## Rule 5 — This rule is a default, not a cage

The rule is suspended whenever the user says so in the current task. Examples:
"you may edit core/", "ignore the scope rules for this", "do a repo-wide refactor",
"set up the project". An explicit user instruction always wins.

When in doubt, ask. Silence is not permission.

## Rule 6 — Report what you touched

End every task by listing the files you wrote. If you touched anything outside your
section, call it out and name the permission that covered it.
