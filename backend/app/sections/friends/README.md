# Friends

The user's friend list, shown in the sheet behind the **Friends** / **Add friend**
buttons on the friends feed.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/friends`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/ping` | health check |
| GET | `?user_id=` | the user's friends, most recently added first |
| POST | | add a friend by email (`{user_id, email, name?}`) — `201`, `409` if already added |
| DELETE | `/{friend_id}?user_id=` | remove a friend — `204`, `404` if not on the list |

Rules:

- **A friend is a contact, not an account.** The row stores `friend_name` +
  `friend_email` and the user owns it, so any address can be added — no lookup in
  `auth.users`, no fictional Supabase accounts, nothing to accept or confirm.
- **Emails are normalised** (trimmed, lower-cased) before the uniqueness check, so
  `James.May@Example.com ` and `james.may@example.com` are the same friend.
- **Names are derived** when the caller does not send one: `james.may+credit@…`
  becomes *James May*. The API owns that formatting, not the browser.
- **Adding twice is a 409**, not a second row (`unique (user_id, friend_email)`;
  a race that slips past the pre-check is caught as a Postgres `23505`).
- Validation is a loose pydantic `pattern` rather than `EmailStr`, because
  `EmailStr` would pull in `email-validator` — a new deployment dependency.

## Database

Run [`schema.sql`](./schema.sql) once in the Supabase SQL editor. One table:

- `friends` — `user_id`, `friend_name`, `friend_email`, `created_at`; unique on
  `(user_id, friend_email)`, indexed on `(user_id, created_at desc)`, own-row RLS
  policies.

Until it exists the endpoints return **503 `database_not_ready`** (PGRST205),
which the UI shows as an API error.

## Seeding the demo friends

```powershell
cd backend
..\.venv\Scripts\python.exe -m app.sections.friends.seed          # demo@demo.com
..\.venv\Scripts\python.exe -m app.sections.friends.seed <uuid>   # any user
```

Upserts the eight people from `content.py` (the same names the feed shows), so it
is safe to re-run. `backend/scripts/seed_demo.py` also calls `run()` as part of the
full demo seed.

## Auth

There is no JWT dependency yet: the router takes an explicit `user_id` and injects
the service-role client, with every repository query filtered by `user_id`.
`TODO(friends)`: switch to `get_supabase` + the JWT subject once auth exists.

## TODOs

- [ ] Real friendships: mirror rows against `auth.users` ids and require the other
      person to accept before they appear.
- [ ] Show each friend's real feed activity (today the feed fixtures are hardcoded
      in `friends_feed/content.py`).
- [ ] Invite by email (send a message rather than silently storing a contact).
- [ ] Search / pagination once a user has more than a screenful of friends.
