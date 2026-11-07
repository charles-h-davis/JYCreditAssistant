"""Credit Learning section — a five-part roadmap that teaches how credit works.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

Users work through 15 short lessons (5 categories × 3 lessons), each with a
summary and five multiple-choice questions. Content lives in the database;
per-user progress, retakes and a daily streak live next to it.

## Roadmap content

| # | Category (`id`) | Lessons |
| --- | --- | --- |
| 1 | `credit-basics` — Credit Basics | What credit is · Credit reports & scores · Cards vs loans |
| 2 | `financial-arithmetic` — Financial Arithmetic | Interest & APR · Compound interest & minimums · Amortisation & total cost |
| 3 | `budgeting-and-affordability` — Budgeting and Affordability | Income & cash flow · Needs/wants & emergency buffer · Debt-to-income |
| 4 | `comparing-credit-options` — Comparing Credit Options | APR, fees & total cost · 0% offers & transfers · Secured/credit-building |
| 5 | `managing-repayments` — Managing Repayments | Statement cycles (closing/day) · Minimum vs full · Payoff strategies & late fees |

Content is authored in `content/` (typed dataclasses, one module per category)
and loaded into Supabase by `seed.py`.

## Endpoints (`/api/v1/credit-learning`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/ping` | health check |
| GET | `/roadmap?user_id=` | 5 categories → 3 lessons with completed/attempts/best score + streak |
| GET | `/lessons` | flat catalogue with question counts |
| GET | `/lessons/{slug}` | summary + 5 questions (**no correct answers**) |
| POST | `/lessons/{slug}/attempt` | grade answers, mark completed, extend streak |
| GET | `/progress?user_id=` | completed lessons with stats + streak |
| GET | `/recap?user_id=` | 5 random questions from lessons the user completed |
| POST | `/recap/attempt` | grade a recap round (counts for the streak) |

Rules:

- **Any** submitted lesson attempt completes the lesson — 100% is not required.
  Retakes are unlimited: attempts increment, `best_score` is kept.
- Streaks count consecutive **days** with a lesson **or recap** submission (UTC).
  A missed calendar day resets the visible streak to 0 (computed lazily); the
  next submission starts a new streak at 1.
- Recap draws from **lessons completed at least once** — correctness of past
  answers is irrelevant.

## Database

Run [`schema.sql`](./schema.sql) once in the Supabase SQL editor. Tables:

- `learning_categories`, `learning_lessons`, `learning_questions` — public read.
- `learning_completions` — one row per `(user_id, lesson_id)` with attempt stats.
- `learning_attempts` — every graded submission (`kind = lesson | recap`).
- `learning_streaks` — `current_streak`, `longest_streak`, `last_activity_date`.

## Seeding content

After `schema.sql` (idempotent; rerun after editing `content/`):

```powershell
..\.venv\Scripts\python.exe -m app.sections.credit_learning.seed
```

Expected: 5 categories, 15 lessons, 75 questions.

## Auth

There is no JWT dependency yet: user-scoped endpoints take an explicit
`user_id` and the router injects the service-role Supabase client, with every
repository query filtered by `user_id`. `TODO(credit_learning)`: switch to
`get_supabase` + the JWT subject once auth exists.

## TODOs

- [ ] Replace `user_id` parameters with the Supabase JWT subject.
- [ ] Optional: store per-question responses for richer recap analytics.
- [ ] Daily streak reminders / webhook of missed days.
- [ ] Per-category progress badges in the frontend (data already available).

