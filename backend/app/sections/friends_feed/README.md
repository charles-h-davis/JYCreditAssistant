# Friends Feed

The social feed behind the **Friends feed** button on the Learning tab: fictional
friend activity mixed with the signed-in user's own finished lessons and refresh
rounds, newest first.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/friends-feed`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/ping` | health check |
| GET | `/feed?user_id=&limit=` | friend activity + the user's own entries, newest first (`limit` 1-40, default 12) |
| POST | `/entries` | record a finished lesson or refresh round |

Rules:

- **Every event is a stored row.** `GET /feed` is a plain read of
  `friends_feed_entries` ordered by `created_at desc` — nothing is invented,
  merged or timestamped at request time.
- **Two kinds of row share the table.** The user's own activity is written by the
  app (`actor = "You"`, after an attempt has been graded); their friends' activity
  is written once by [`seed.py`](./seed.py) (`actor = <friend name>`), using the
  friends from the `friends` table and real lesson titles from Credit Learning.
  `is_self` is derived from the actor, not stored twice.
- **Newest first, cut to size.** The endpoint returns at most `limit` rows
  (default 12, hard cap 40), so the response is always the latest entries.
- **Re-running the seed replaces the friend activity** and leaves the user's own
  completions untouched, so the demo stays reproducible without losing history.
- **The API owns the wording.** The client sends `kind`, `lesson_title`, `score`
  and `total`; the service composes `completed <lesson>` / `finished a refresh
  round` plus a `<score>/<total> correct` detail.

## Database

Run [`schema.sql`](./schema.sql) once in the Supabase SQL editor (after
`credit_learning/schema.sql` and `friends/schema.sql`). One table:

- `friends_feed_entries` — `user_id`, `kind` (`lesson` | `recap` | `streak`),
  `actor`, `action`, `detail`, `created_at`; append-only, indexed on
  `(user_id, created_at desc)` with own-row RLS policies.

Until it exists, `/feed` and `/entries` return **503 `database_not_ready`**
(PostgREST `PGRST205`), which the UI shows as an API error.

## Generating friend activity

```powershell
cd backend
..\.venv\Scripts\python.exe -m app.sections.friends_feed.seed          # demo@demo.com
..\.venv\Scripts\python.exe -m app.sections.friends_feed.seed <uuid>   # any user
```

One event per friend plus a few extras (streaks, refresh rounds and completed
lessons), spread over the last three days. Run `app.sections.friends.seed` first —
without friends there is nobody to generate activity for. `backend/scripts/seed_demo.py`
calls both as part of the full demo seed.

## Auth

There is no JWT dependency yet: the router takes an explicit `user_id` and injects
the service-role client, with every repository query filtered by `user_id`.
`TODO(friends_feed)`: switch to `get_supabase` + the JWT subject once auth exists.

## TODOs

- [ ] Real friendships: a `friends` table plus a policy that widens `/feed` past
      the caller's own rows.
- [ ] Record streak milestones ("achieved a 10 day streak") as entries too.
- [ ] Reactions / kudos on an entry.
- [ ] Paginate with a cursor instead of the flat `limit`.
