# CreditMate

A mobile-first web app that helps people understand, manage and pay down credit card
debt — and makes credit less intimidating to get into..

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
| Dashboard | `/dashboard` | card-storage, cost-to-buy, credit-learning, notifications |
| Transactions | `/transactions` | card-storage |
| Learning | `/learning` | credit-learning |
| Friends feed | `/friends-feed` | friends-feed |
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
| Friends | `/api/v1/friends` | _fill in_ |
| Friends Feed | `/api/v1/friends-feed` | _fill in_ |
| Notifications | `/api/v1/notifications` | _fill in_ |

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
transactions, planned purchases, learning progress, friends and a few days of
friend activity for the feed by `backend/scripts/seed_demo.py` (re-runnable; it
resets only the demo user's rows).
`backend/scripts/verify_demo.py` hits every endpoint the UI uses and prints a
pass/fail line per call. See [`frontend/README.md`](frontend/README.md) for the
one-time `cost_to_buy/schema.sql` step.

## Deploy on Vercel

The repo deploys as **one Vercel project with two services**. `vercel.json` at the root
declares both, and the public rewrites decide what the internet can reach:

| Public path | Service | What it is |
| --- | --- | --- |
| `/api/(.*)` | `backend` | FastAPI — `backend/`, entrypoint `app.main:app` |
| `/health` | `backend` | Liveness probe (`GET /health`) |
| everything else | `frontend` | Next.js app — `frontend/` |

Each service is built independently. A rewrite keeps the original path, so
`/api/v1/card-storage/cards` reaches exactly the route that runs locally; in production
the frontend calls the same-origin `/api/v1` (`frontend/src/lib/config.ts`) and nothing
has to know a hostname. `/docs` is intentionally **not** routed publicly — add a rewrite
above the catch-all if you want the API contract on the public domain.

**No service bindings.** Every API call is made by the browser here: every screen is
`"use client"` and there is no middleware, route handler or server-side `fetch`. Service
bindings resolve inside functions only — never in the browser — so the public `/api`
rewrite is the link between the two services and a binding would change nothing at
runtime. If a server-side proxy is ever added, declare the binding on the *calling*
service and read the injected variable instead of a hostname:

```json
"bindings": [{ "type": "service", "service": "backend", "format": "url", "env": "BACKEND_URL" }]
```

### Local multi-service run

```powershell
npx vercel dev      # both services on one port, like production (needs `npm i -g vercel`)
```

`npm run dev` + `uvicorn` still works and is faster for frontend-only work; the app falls
back to `http://127.0.0.1:8000/api/v1` outside production builds.

### Environment variables

Set these on the Vercel project — services share the project's environment variables:

| Variable | Read by | Notes |
| --- | --- | --- |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | backend | service-role key is backend-only, never sent to the browser |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | backend | photo extraction + assistant |
| `OPENAI_API_KEY` | backend | reserved for the assistant |
| `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV` | backend | card sync (sandbox) |
| `APP_ENV` | backend | set to `production` |
| `CORS_ORIGINS` | backend | `https://<your-domain>`; a no-op while the API is same-origin, kept for direct callers |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | inlined at build time |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | optional — leave unset to use the same-origin `/api/v1` |
| `NEXT_PUBLIC_DEMO_EMAIL`, `NEXT_PUBLIC_DEMO_PASSWORD` | frontend | the one-tap demo sign-in |

Vercel runs Python 3.12 by default, which is what `backend/pyproject.toml` asks for
(`requires-python = ">=3.12"`). Run `backend/scripts/seed_demo.py` once against the same
Supabase project before demoing — the seeded account is not part of the deployment.

### Two deployment gotchas

- **Request bodies are capped at 4.5 MB** by Vercel Functions. The purchase photo step
  therefore re-encodes in the browser before uploading (`frontend/src/lib/images.ts`:
  long edge 1600 px, ≤3.5 MB, JPEG) instead of posting the raw 3–12 MB camera file.
  HEIC/HEIF photos are passed through untouched because Chrome cannot decode them, so
  those still rely on the API's own 10 MB limit.
- **`backend/pyproject.toml` mirrors `requirements.txt`.** Vercel's Python builder
  prefers `pyproject.toml` when both exist and there is no lockfile, so a `pyproject.toml`
  without a `[project]` table silently installs no dependencies. Keep the two lists
  identical when bumping a version.

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
vercel.json      Vercel project: `backend` + `frontend` services and their public routes
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
