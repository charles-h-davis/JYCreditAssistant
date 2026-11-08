# CreditMate

A mobile-first web app that helps people understand, manage and pay down credit card
debt — and makes credit less intimidating to get into.

## Stack

| Layer | Tech |
| --- | --- |
| Backend | Python + FastAPI (`backend/`) |
| Database + Auth | Supabase (Postgres + Auth) |
| Frontend | React 19 + Next.js 16 + Tailwind v4 (`frontend/`) |

## Status

**Phase 1 — backend:** complete. Each product area is its own FastAPI section, built
and tested independently.

**Phase 2 — frontend:** built. A mobile-first Next.js app in `frontend/` wired to the
API, following the screens in `frontend/design refs/`.

| Screen | Route | API |
| --- | --- | --- |
| Sign in / create account | `/sign-in` | Supabase Auth |
| Dashboard | `/dashboard` | card-storage, cost-to-buy, credit-learning |
| Transactions | `/transactions` | card-storage |
| Learning | `/learning` | credit-learning |
| Lesson / refresh round | `/learning/lesson/[slug]`, `/learning/recap` | credit-learning |
| Your Account | `/account` | card-storage, cost-to-buy |
| Check a purchase → photo → details → total cost | `/purchase/**` | cost-to-buy |
| Ask Me Anything | `/assistant` | ai-assistant |

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

Frontend (second terminal):

```powershell
cd frontend
npm install
copy .env.local.example .env.local   # fill in the Supabase URL + anon key
npm run dev                          # http://localhost:3000
```

**Demo account:** `demo@demo.com` / `demo123!` — created and filled with cards,
transactions, planned purchases and learning progress by
`backend/scripts/seed_demo.py` (re-runnable; it resets only the demo user's rows).
`backend/scripts/verify_demo.py` hits every endpoint the UI uses and prints a
pass/fail line per call. See [`frontend/README.md`](frontend/README.md) for the
one-time `cost_to_buy/schema.sql` step.

## Repository layout

```
.clinerules/     Rules for AI agents — read 10-write-scope.md before editing
.agents/skills/  Installed agent skills, shared with the team
skills-lock.json What `npx skills` installed and from where (commit this)
backend/         FastAPI service (see backend/README.md)
  scripts/       seed_demo.py (demo account) + try_cost_to_buy.py
frontend/        Next.js mobile app (see frontend/README.md)
  design refs/   the screens the UI was built from
  scripts/       screenshot.py — Playwright pass over every screen
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
