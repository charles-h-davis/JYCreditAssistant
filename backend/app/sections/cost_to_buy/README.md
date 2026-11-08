"""Cost to Buy section — the true cost of a credit purchase.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

Answers "what will this purchase really cost me?" in two steps: read a product name
and price out of a photo, then show how the purchase changes the payoff of an
existing card balance at the user's current monthly payment — with a slider of
adjusted payments.

## Endpoints (`/api/v1/cost-to-buy`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| POST | `/extract` | implemented (Gemini vision, multipart image) |
| POST | `/estimate` | implemented (single-balance amortisation, stateless) |
| POST | `/purchase-impact` | implemented (extra cost of a purchase, stateless) |
| GET | `/purchase-plans?user_id=` | implemented (DB) |
| POST | `/purchase-plans` | implemented (confirm: store plan + set payment) |
| DELETE | `/purchase-plans/{plan_id}?user_id=` | implemented (DB) |
| GET | `/monthly-payment?user_id=&card_id=` | implemented (DB) |
| PUT | `/monthly-payment` | implemented (DB, upsert) |

`user_id` is the Supabase auth user UUID. It is a temporary stand-in for a JWT
dependency (the API has no auth yet); the router injects the service-role client
and every repository query filters on `user_id`.

## Modelling

- Money is GBP; APR is a percent (`24.99` = 24.99%).
- The billing cycle is anchored on **`closing_day`** (the statement-close day): at
  each close the payment for the cycle is applied first, then `APR/12` of whatever
  is **left** is added as interest.
- The monthly payment is applied on **`statement_day`** (the due day); the payoff
  date is the due date on which the balance reaches zero.
- Paying the balance off **in full** therefore costs no interest and settles the
  card in a single cycle — which is why the payment slider's maximum (the whole
  balance) reports "debt free in 1 month".
- Charging interest on the remaining balance also keeps the maths **monotone**:
  raising the monthly payment can only ever lower the total cost of an item, never
  bump it up at a cycle boundary. `test_item_cost_falls_as_the_payment_rises`
  sweeps the range to guarantee it.
- The headline number is `extra_total_paid` — total currency paid *with* the
  purchase minus *without* it (this is the item price plus the extra interest). The
  response also reports `extra_interest` and `extra_months`, plus a `scenarios`
  ladder the "adjust your payment" screen can render.
- The maths lives in `service.py` as pure functions so it is unit-testable without a
  database.

## Environment (`backend/.env`, gitignored — see `.env.example`)

```
GEMINI_API_KEY=          # https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash-lite
```

`POST /extract` returns **503 `gemini_not_configured`** when the key is missing.

## Database

Run [`schema.sql`](./schema.sql) once in the Supabase SQL editor **after** the
card-storage schema (both tables reference `public.credit_cards`). It creates:

- `purchase_plans` — `id`, `user_id`, `card_id`, `product_name`, `purchase_amount`,
  `currency`, `monthly_payment`, `months_to_payoff`, `total_interest`, `created_at`.
- `card_payment_settings` — `id`, `user_id`, `card_id`, `monthly_payment`,
  `created_at`, `updated_at`, `unique(user_id, card_id)`.

RLS is `user_id = auth.uid()` on both; the backend bypasses it with the service role
until auth exists but still filters on `user_id`.

**Confirm-purchase flow:** `POST /purchase-plans` inserts the plan *and* upserts
`card_payment_settings.monthly_payment` in one call, so the card's current payment
becomes the value the user confirmed on the "adjust payment" screen.

## Rules

- `card_storage` owns the cards; read card data through that section, never by
  querying `credit_cards` from here.
- Reject full card numbers / CVV / expiry. The extraction prompt tells the model to
  ignore payment credentials.
- PDFs/other files: only `image/png|jpeg|webp|heic|heif` are accepted (415), capped
  at 10 MB (413).

## TODOs

- [ ] Replace `user_id` query/body parameters with the Supabase JWT subject and
      switch to the anon client + RLS.
- [ ] Read `current_balance` / `purchase_apr` / `closing_day` from `credit_cards`
      (via card-storage) instead of taking them in the request body.
- [ ] Add delete/list-per-card endpoints if the UI needs them.
"""
