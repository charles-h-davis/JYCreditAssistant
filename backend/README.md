# CreditMate — Backend

FastAPI service for CreditMate. Phase 1 of the project: the API is built
section by section, then the Next.js frontend is wired up to it.

## Quickstart

The virtualenv lives at the repo root (`.venv`), so commands run from `backend/`:

```powershell
# 1. install dependencies
..\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# 2. configure secrets (backend/.env already exists with blanks)
#    copy .env.example -> .env and fill in SUPABASE_URL / keys

# 3. run the API
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# 4. test + lint
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m ruff check .
```

- Interactive docs (the frontend contract): http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

On macOS/Linux the interpreter is `.venv/bin/python`, so use
`../.venv/bin/python -m ...` from `backend/`.

## Layout

```
app/
  main.py            app factory: CORS, /health, mounts every section router
  core/              settings, Supabase clients, shared error types   (lead-owned)
  sections/          one package per product section                 (one owner each)
    cost_to_buy/       /api/v1/cost-to-buy
    credit_learning/   /api/v1/credit-learning
    card_storage/      /api/v1/card-storage
    ai_assistant/      /api/v1/ai-assistant
tests/               pytest: app smoke tests + one file per section
```

Each section follows the same shape (`router.py` → `service.py` → `repository.py`,
plus `schemas.py` and a `README.md` listing its tables and TODOs). `app/sections`
auto-discovers any child package exposing a `router`, so adding endpoints never
requires editing `main.py`.

## Conventions

See `.clinerules/20-backend-conventions.md` for the full list. The short version:

- Routers handle HTTP only; business logic in `service.py`; Supabase in `repository.py`.
- Never import `os.environ` — use `app.core.config.settings`.
- Never build a Supabase client by hand — inject `get_supabase` / `get_supabase_admin`.
- Money is USD, APR is a percent (`24.99` = 24.99%).
- Unimplemented endpoints return **501**, never fake data.

## Working in parallel

`.clinerules/10-write-scope.md` defines the rule: write only inside your own
section (`app/sections/<yours>/` + `tests/sections/test_<yours>.py`), read anything,
and ask for permission before touching shared files.
