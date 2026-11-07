# JY Credit Assistant — Project Context

Mobile-first web app that helps people understand, manage and pay down credit card
debt, and makes credit more accessible. Two developers, hackathon build.

## Stack

| Layer | Tech |
| --- | --- |
| Backend | Python 3.12+ / FastAPI (`backend/`) |
| Data + Auth | Supabase (Postgres + Auth, accessed via `supabase-py` / PostgREST) |
| Frontend | React + Next.js + Tailwind — **phase 2 only** (`frontend/`) |

## Phases

1. **Now — backend only.** Build and stabilise the API contract per section. Do not
   scaffold or edit frontend code yet.
2. **Later — frontend.** Next.js app in `frontend/`, wired to the finished API.

## Repo map

```
.clinerules/                  Rules for AI agents (read these before editing)
.agents/skills/               Installed agent skills (committed, shared with the team)
backend/
  app/main.py                 FastAPI app factory: CORS, /health, mounts every section router
  app/core/                   Shared infrastructure: config, Supabase clients, error types
  app/sections/               One Python package per product section (see table below)
  tests/                      Pytest smoke tests, one file per section
frontend/                     Phase 2 (placeholder only)
```

## Backend sections

Each section is a self-contained FastAPI package under `backend/app/sections/<name>/`
and owns its own tables, schemas, logic and tests.

| Section | Python package | URL prefix | Owner |
| --- | --- | --- | --- |
| Cost to Buy | `cost_to_buy` | `/api/v1/cost-to-buy` | _fill in_ |
| Credit Learning | `credit_learning` | `/api/v1/credit-learning` | _fill in_ |
| Card Storage | `card_storage` | `/api/v1/card-storage` | _fill in_ |
| AI Credit Assistant | `ai_assistant` | `/api/v1/ai-assistant` | _fill in_ |

`app/sections/__init__.py` discovers every child package that exposes an `APIRouter`
named `router` and `main.py` mounts them all under the API prefix. Adding endpoints to
your own section never requires editing `main.py`.

## Commands (run from `backend/`)

```bash
# install (once)
..\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# run the API with reload
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# tests / lint
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m ruff check .
```

Docs: `http://127.0.0.1:8000/docs` · Health: `http://127.0.0.1:8000/health`

## Environment

Secrets live in `backend/.env` (gitignored). See `backend/.env.example` for the keys:
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`,
`APP_ENV`, `CORS_ORIGINS`.

Never commit real keys. The service-role key is backend-only — it must never be sent to
the browser or embedded in the frontend.
