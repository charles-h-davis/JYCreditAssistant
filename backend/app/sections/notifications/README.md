# Notifications

Turns "you already bought the thing you were planning to buy" into a notification:
the bell on the dashboard badges up and lists the suspected matches, and the user
answers each one with **✓** (it happened — drop the plan) or **✗** (not that — keep
the plan, stop asking).

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/notifications`)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/ping` | health check |
| GET | `?user_id=` | `{ count, matches: [...] }` — the badge and the list |
| POST | `/dismissals` | remember a ✗ for one `(plan, transaction)` pair — `201`, idempotent |

## The matching rule

A card transaction is reported against a planned purchase when **all** of these hold:

1. **Same card** — `transaction.card_id == plan.card_id`.
2. **Same amount** — within half a penny (both columns are `numeric(12,2)`).
3. **It is a purchase** — `amount > 0`. Plaid's convention (see
   `card_storage/schema.sql`) is that positive amounts leave the account, so
   refunds and card payments can never match.
4. **On or after the plan date** — `coalesce(authorized_date, posted_date)` is on
   or after the date the plan was **created**. There is no "intended purchase date"
   column, so the plan's creation date is the reference point.
5. **Not dismissed** — the pair is absent from `purchase_match_dismissals`.

Matches are returned newest transaction first, and `count` is simply how many there are.

## The two answers

| Action | What the UI calls | Effect |
| --- | --- | --- |
| **✓** it happened | `DELETE /api/v1/cost-to-buy/purchase-plans/{plan_id}?user_id=` | the planned purchase is removed; the match disappears because the plan did |
| **✗** not that | `POST /api/v1/notifications/dismissals` | the plan stays; that pair never notifies again |

Accepting deliberately writes nothing here — deleting the plan *is* the answer, and
if the follow-up refresh fails the notification still self-heals on the next fetch.

## Database

Run [`schema.sql`](./schema.sql) once in the Supabase SQL editor (after
`card_storage/schema.sql` and `cost_to_buy/schema.sql`). One table:

- `purchase_match_dismissals` — `user_id`, `plan_id`, `transaction_id`,
  `created_at`; unique on the three ids, own-row RLS policies, **no** foreign keys
  (a dismissal has to outlive the plan it refers to).

The section reads two tables it does not own — `purchase_plans` (cost_to_buy) and
`card_transactions` (card_storage) — always filtered by `user_id` and never written.

## Testing it by hand

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000   # separate terminal
..\.venv\Scripts\python.exe scripts\try_notifications.py          # full ✗/✓ walk-through
```

Live-demo version: plan a purchase in the app, then insert a `card_transactions`
row with the same amount, today's date and the same `card_id` — the bell picks it
up within about 15 seconds (the dashboard polls).

## TODOs

- [ ] Window the transaction query once history grows (today it reads the user's
      whole history on each poll).
- [ ] Notify on near-matches (e.g. ±£1 for tips) behind a setting.
- [ ] Push/email delivery instead of an in-app bell.
