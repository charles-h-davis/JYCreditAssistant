"""Business logic for the Cost to Buy section.

Pure functions only: no HTTP, no Supabase, no environment access. That keeps the
credit maths unit-testable without a database.

TODO(cost_to_buy owner):
  - `estimate_purchase_cost(request)` -> monthly amortisation until balance is 0,
    returning total interest, months to payoff and payoff date.
  - Handle the interest-free case (apr == 0) without dividing by zero.
  - Round money to 2 decimals only at the boundary, not inside the loop.
"""

from app.sections.cost_to_buy.schemas import PurchaseCostRequest, PurchaseCostResponse


def estimate_purchase_cost(request: PurchaseCostRequest) -> PurchaseCostResponse:
    """Return the true cost of financing `request.purchase_amount` at `request.apr`."""
    raise NotImplementedError("TODO(cost_to_buy): implement purchase cost amortisation")
