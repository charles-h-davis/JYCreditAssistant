# JY Credit Assistant

A mobile-first web app that helps people understand, manage and pay down credit card
debt — and makes credit less intimidating to get into.

## Stack

| Layer | Tech |
| --- | --- |
| Backend | Python + FastAPI (`backend/`) |
| Database + Auth | Supabase (Postgres + Auth) |
| Frontend | React + Next.js + Tailwind (`frontend/` — phase 2) |

## Status

**Phase 1 — backend.** Each product area is its own FastAPI section, built and tested
independently. The frontend gets wired up once the API contract is stable.

| Section | Base URL | Owner |
| --- | --- | --- |
| Cost to Buy | `/api/v1/cost-to-buy` | _fill in_ |
| Credit Learning | `/api/v1/credit-learning` | _fill in_ |
| Card Storage | `/api/v1/card-storage` | _fill in_ |
| AI Credit Assistant | `/api/v1/ai-assistant` | _fill in_ |

## Get started

```powershell
..\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Then open http://127.0.0.1:8000/docs. Full instructions in
[`backend/README.md`](backend/README.md).

## Repository layout

```
.clinerules/     Rules for AI agents — read 10-write-scope.md before editing
.agents/skills/  Installed agent skills (find-skills), shared with the team
skills-lock.json What `npx skills` installed and from where (commit this)
backend/         FastAPI service (see backend/README.md)
frontend/        Next.js app — phase 2, placeholder for now
```

## Working with AI agents on this repo

Each section has a single owner. Agents must write only inside the section they are
working on, treat everything else as read-only, and ask for permission before touching
shared files (`app/core/`, `app/main.py`, requirements, `.clinerules/`). The full rule
is in [`.clinerules/10-write-scope.md`](.clinerules/10-write-scope.md).

To install more skills for the team:

```powershell
npx skills find "fastapi"
npx skills add <owner/repo@skill>
```

## Environment

Copy `backend/.env.example` to `backend/.env` and fill in the Supabase URL, anon key and
service-role key. `.env` is gitignored — never commit real keys, and never expose the
service-role key to the browser.
