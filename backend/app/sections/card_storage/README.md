"""Card Storage section — where a user's credit cards live.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/card-storage`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| GET | `/cards` | **stub → 501** |
| POST | `/cards` | **stub → 501** |

## Supabase

Table: `credit_cards` — suggested columns: `id` (uuid pk), `user_id` (uuid, fk →
`auth.users`), `nickname`, `issuer`, `last_four` (char(4)), `credit_limit` (numeric),
`current_balance` (numeric), `apr` (numeric), `statement_day` (smallint),
`due_day` (smallint), `is_secured` (bool), `created_at`, `updated_at`.

RLS: `user_id = auth.uid()` on every operation. Never allow `select` across users —
this table is someone's financial life.

## Rules

- Store metadata only. Reject anything that looks like a full card number, CVV or
  expiry — we are not a payment processor and must not hold card credentials.
- Money is `numeric` in Postgres and `float` in the API, rounded to 2dp.
- Correlating to other sections: other sections read cards through *this* section's
  service, never by querying `credit_cards` themselves.

## TODOs

- [ ] Create the `credit_cards` table + RLS policy in Supabase.
- [ ] Implement `repository` functions, then `service`, then wire the router.
- [ ] Add an auth dependency so `user_id` comes from the Supabase JWT.
- [ ] Add update/delete endpoints.
