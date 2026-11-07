"""Card Storage section — where a user's credit cards live.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

Loads a specified client's cards from the **Plaid sandbox** into Supabase, and
stores transaction history alongside them.

## Endpoints (`/api/v1/card-storage`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| GET | `/cards?user_id=` | implemented |
| POST | `/cards?user_id=` | implemented (manual card) |
| GET | `/cards/{card_id}/transactions?user_id=` | implemented |
| POST | `/plaid/sync` | implemented (Plaid sandbox → database) |

`user_id` is the Supabase auth user UUID. It is a temporary stand-in for a JWT
dependency (the API has no auth yet), and the router injects the service-role
client; every repository query filters on `user_id`.

## Field naming (product wording)

- `closing_day` — day of month the statement **closes** (statement day).
- `statement_day` — day of month the **payment is due** (due date).

## Environment (`backend/.env`, gitignored — see `.env.example`)

```
PLAID_CLIENT_ID=
PLAID_SECRET=
PLAID_ENV=sandbox
PLAID_SANDBOX_INSTITUTION_ID=ins_56
PLAID_ACCESS_TOKEN=        # optional: reuse an existing sandbox Item
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
```

`POST /plaid/sync` uses, in order: the request's `access_token`, then
`PLAID_ACCESS_TOKEN`, then a fresh sandbox Item created via
`/sandbox/public_token/create` + `/item/public_token/exchange`.
Missing Plaid keys return **503**; Plaid failures return **502**.

## Database

Run [`schema.sql`](./schema.sql) once in the Supabase SQL editor. It creates
`plaid_items` (access tokens, backend-only), `credit_cards` and
`card_transactions` with RLS (`user_id = auth.uid()`) and `updated_at` triggers.

Upsert keys make syncs idempotent: `plaid_items.item_id`,
`(credit_cards.user_id, plaid_account_id)`, `card_transactions.plaid_transaction_id`.

## Plaid → column mapping

| Column | Plaid source |
| --- | --- |
| `closing_day` | day of `liabilities.credit[].last_statement_issue_date` |
| `statement_day` | day of `liabilities.credit[].next_payment_due_date` |
| `purchase_apr` | `liabilities.credit[].aprs[]` where `apr_type = purchase_apr` |
| `credit_limit` | `accounts[].balances.limit` |
| `current_balance` | `accounts[].balances.current` (current debt) |
| `available_balance` | `accounts[].balances.available` |
| `last_four` | `accounts[].mask` |
| `issuer` | `accounts/item.institution_name` |
| `card_transactions.*` | `/transactions/sync` `added`/`modified`/`removed` |

Only `type == "credit"` accounts become cards. Money is `numeric(12,2)` in
Postgres and `float` round to 2dp in the API; APR is a percent (`24.99` =
24.99%). Transaction amounts keep Plaid's sign: positive = money left the account.

## Loading a real sandbox client

1. Fill the Supabase + Plaid keys in `backend/.env`.
2. Run `schema.sql` in the Supabase SQL editor.
3. Create a user (Supabase Auth dashboard) and copy its UUID.
4. `POST /api/v1/card-storage/plaid/sync` with `{"user_id": "<uuid>"}`
   (optionally `institution_id` / `access_token`).
5. Read it back with `GET /api/v1/card-storage/cards?user_id=<uuid>`.

## Rules

- Store metadata only. Reject anything that looks like a full card number, CVV or
  expiry — we are not a payment processor and must not hold card credentials.
- Never return `plaid_items.access_token` from an endpoint or log it.
- Correlating to other sections: other sections read cards through *this*
  section's service, never by querying `credit_cards` themselves.

## TODOs

- [ ] Replace `user_id` query/body parameters with the Supabase JWT subject and
      switch to the anon client + RLS.
- [ ] Add update/delete card endpoints.
- [ ] Handle Plaid `SYNC_UPDATES_AVAILABLE` webhooks for background refreshes.
- [ ] Support multiple Items per user in the UI (the backend already does).
