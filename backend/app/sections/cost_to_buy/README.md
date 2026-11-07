"""Cost to Buy section — the true cost of a credit purchase.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/cost-to-buy`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| POST | `/estimate` | **stub → 501** |

## Supabase

Table: `purchase_plans` — suggested columns: `id` (uuid pk), `user_id` (uuid, fk →
`auth.users`), `label`, `purchase_amount` (numeric), `apr` (numeric),
`monthly_payment` (numeric), `months_to_payoff` (int), `total_interest` (numeric),
`created_at`.

RLS: `user_id = auth.uid()` on every operation.

## Notes

The estimate maths is pure and should stay in `service.py` so it can be unit tested
without a database. Percentages are percents: `24.99` means 24.99%.

## TODOs

- [ ] Implement `service.estimate_purchase_cost` (monthly amortisation, apr = 0 safe).
- [ ] Wire `POST /estimate` to the service.
- [ ] Create the `purchase_plans` table + RLS, then implement `repository`.
- [ ] Add save/list endpoints for plans once the calculator works.
