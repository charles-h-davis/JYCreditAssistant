"""Business logic for the Cost to Buy section.

The maths is pure (no HTTP, no Supabase, no environment access) so the credit
calculations are unit-testable without a database. Persistence and the Gemini call
take injected collaborators so tests can pass fakes.

Modelling (see the section README):

- Interest is assessed each billing cycle anchored on ``closing_day`` (the
  statement-close day): the outstanding balance is multiplied by ``APR/12`` and the
  interest is added at the close.
- The monthly payment is applied on ``statement_day`` (the due day). The payoff
  date is the due date on which the balance reaches zero.
- There is no grace period: a carried balance accrues interest every cycle,
  including the cycle in which the new purchase is added.
"""

import math
from datetime import date
from functools import lru_cache
from pathlib import Path

from supabase import Client

from app.core.exceptions import NotFoundError
from app.sections.cost_to_buy import repository
from app.sections.cost_to_buy.gemini_client import GeminiClient
from app.sections.cost_to_buy.schemas import (
    ExtractResponse,
    MonthlyPaymentRead,
    PaymentScenario,
    PayoffSummary,
    PurchaseCostRequest,
    PurchaseCostResponse,
    PurchaseImpactRequest,
    PurchaseImpactResponse,
    PurchasePlanCreate,
    PurchasePlanRead,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"
#: Safety cap so a payment that never clears the interest cannot loop forever.
MAX_CYCLES = 1200  # 100 years of monthly cycles
#: Default horizon used when a caller omits ``monthly_payment``.
DEFAULT_SUGGESTED_MONTHS = 24
#: Multipliers for the "adjust your monthly payment" scenarios.
DEFAULT_SCENARIO_MULTIPLIERS = (1.0, 1.1, 1.25, 1.5, 2.0)


def monthly_rate(purchase_apr: float) -> float:
    """Return the per-cycle interest rate from an APR percent."""
    return (purchase_apr / 100) / 12


def _round(value: float) -> float:
    """Round money to two decimals at the boundary."""
    return round(value, 2)


def _clamp_day(year: int, month: int, day: int) -> date:
    """Build a date, clamping `day` to the month's length (handles 29-31 Feb etc.)."""
    last_day = _days_in_month(year, month)
    return date(year, month, min(day, last_day))


def _days_in_month(year: int, month: int) -> int:
    """Return the number of days in a month without importing `calendar`."""
    if month == 12:
        return 31
    first_of_next = date(year, month + 1, 1)
    return (first_of_next - date(year, month, 1)).days


def _add_months(anchor: date, months: int, day: int) -> date:
    """Return `day` (clamped) in the month `months` after `anchor`'s month."""
    index = anchor.month - 1 + months
    year = anchor.year + index // 12
    month = index % 12 + 1
    return _clamp_day(year, month, day)


def _next_occurrence(anchor: date, day: int) -> date:
    """First date on/after `anchor` whose day-of-month is `day` (clamped)."""
    candidate = _clamp_day(anchor.year, anchor.month, day)
    if candidate < anchor:
        candidate = _add_months(anchor, 1, day)
    return candidate


def _payoff_date(
    anchor: date, cycles: int, closing_day: int | None, statement_day: int | None
) -> date | None:
    """Concrete payoff date (a due day) for a schedule starting at `anchor`.

    The schedule begins at the next statement close (``closing_day``) and the final
    payment lands on a ``statement_day``. Requires ``statement_day``.
    """
    if statement_day is None:
        return None
    schedule_start = _next_occurrence(anchor, closing_day) if closing_day else anchor
    return _add_months(schedule_start, cycles, statement_day)


def suggest_payment(
    balance: float, purchase_apr: float, *, months: int = DEFAULT_SUGGESTED_MONTHS
) -> float:
    """Payment that clears `balance` in `months` cycles at `purchase_apr` (rounded up)."""
    if balance <= 0:
        return 0.0
    rate = monthly_rate(purchase_apr)
    if rate == 0:
        raw = balance / months
    else:
        factor = (1 + rate) ** -months
        raw = balance * rate / (1 - factor)
    # Round up to the cent so the balance always clears within `months`.
    return math.ceil(raw * 100) / 100


def amortize(
    balance: float,
    purchase_apr: float,
    monthly_payment: float,
    *,
    closing_day: int | None = None,
    statement_day: int | None = None,
    start_date: date | None = None,
    max_cycles: int = MAX_CYCLES,
) -> PayoffSummary:
    """Amortise `balance` at `purchase_apr`, paying `monthly_payment` per cycle.

    Interest is posted at the statement close (``closing_day``) on whatever is left
    after the payment, and the payment is applied at the due day
    (``statement_day``); ``payoff_date`` is the due date on which the balance
    reaches zero (needs ``statement_day``).

    Interest on the *remaining* balance (rather than on the whole balance before
    the payment) is what makes paying a card off in full cost nothing in interest,
    and it keeps the curve continuous: raising the payment can only ever lower the
    total interest, never bump it up a cycle boundary.
    """
    if balance <= 0:
        return PayoffSummary(
            months_to_payoff=0, total_interest=0.0, total_paid=0.0, payoff_date=None
        )
    if monthly_payment <= 0:
        raise ValueError("monthly_payment must be greater than zero.")

    if monthly_payment >= balance:
        # Clearing the balance in full settles it that cycle: no further interest.
        return PayoffSummary(
            months_to_payoff=1,
            total_interest=0.0,
            total_paid=_round(float(balance)),
            payoff_date=_payoff_date(
                start_date or date.today(), 1, closing_day, statement_day
            ),
        )

    rate = monthly_rate(purchase_apr)
    if rate > 0 and monthly_payment <= balance * rate:
        raise ValueError(
            "monthly_payment is too low to cover the monthly interest on this balance."
        )

    outstanding = float(balance)
    total_interest = 0.0
    cycles = 0

    while outstanding > 0 and cycles < max_cycles:
        cycles += 1
        if monthly_payment >= outstanding:
            outstanding = 0.0
            break
        remaining = outstanding - monthly_payment
        interest = remaining * rate
        total_interest += interest
        outstanding = remaining + interest
        if outstanding < 0.005:  # guard against float dust leaving a penny behind
            outstanding = 0.0

    if outstanding > 0:
        raise ValueError(
            "monthly_payment is too low to repay this balance within the modelled horizon."
        )

    total_interest = _round(total_interest)
    payoff_date = _payoff_date(start_date or date.today(), cycles, closing_day, statement_day)
    return PayoffSummary(
        months_to_payoff=cycles,
        total_interest=total_interest,
        total_paid=_round(float(balance) + total_interest),
        payoff_date=payoff_date,
    )


def estimate_purchase_cost(request: PurchaseCostRequest) -> PurchaseCostResponse:
    """Return the true cost of financing `request.purchase_amount` at its APR."""
    payment = request.monthly_payment or suggest_payment(
        request.purchase_amount, request.purchase_apr
    )
    summary = amortize(
        request.purchase_amount,
        request.purchase_apr,
        payment,
        closing_day=request.closing_day,
        statement_day=request.statement_day,
        start_date=request.start_date,
    )
    return PurchaseCostResponse(
        purchase_amount=_round(request.purchase_amount),
        purchase_apr=request.purchase_apr,
        monthly_payment=_round(payment),
        months_to_payoff=summary.months_to_payoff,
        total_interest=summary.total_interest,
        total_paid=summary.total_paid,
        payoff_date=summary.payoff_date,
    )


def _default_scenarios(payment: float) -> list[float]:
    """A sensible ladder of larger monthly payments around `payment`."""
    values = {_round(payment * multiplier) for multiplier in DEFAULT_SCENARIO_MULTIPLIERS}
    return sorted(values)


def purchase_impact(request: PurchaseImpactRequest) -> PurchaseImpactResponse:
    """Compare the current plan with the same plan plus the new purchase."""
    schedule = {
        "closing_day": request.closing_day,
        "statement_day": request.statement_day,
        "start_date": request.start_date,
    }
    baseline = amortize(
        request.current_balance,
        request.purchase_apr,
        request.current_monthly_payment,
        **schedule,
    )
    with_purchase = amortize(
        request.current_balance + request.purchase_amount,
        request.purchase_apr,
        request.current_monthly_payment,
        **schedule,
    )

    scenario_payments = request.payment_scenarios or _default_scenarios(
        request.current_monthly_payment
    )
    scenarios: list[PaymentScenario] = []
    for payment in scenario_payments:
        summary = amortize(
            request.current_balance + request.purchase_amount,
            request.purchase_apr,
            payment,
            **schedule,
        )
        scenarios.append(
            PaymentScenario(
                monthly_payment=_round(payment),
                months_to_payoff=summary.months_to_payoff,
                total_interest=summary.total_interest,
                extra_total_paid=_round(summary.total_paid - baseline.total_paid),
                payoff_date=summary.payoff_date,
            )
        )

    return PurchaseImpactResponse(
        currency=request.currency,
        current_balance=_round(request.current_balance),
        purchase_apr=request.purchase_apr,
        purchase_amount=_round(request.purchase_amount),
        current_monthly_payment=_round(request.current_monthly_payment),
        baseline=baseline,
        with_purchase=with_purchase,
        extra_total_paid=_round(with_purchase.total_paid - baseline.total_paid),
        extra_interest=_round(with_purchase.total_interest - baseline.total_interest),
        extra_months=max(0, with_purchase.months_to_payoff - baseline.months_to_payoff),
        scenarios=scenarios,
        assumptions=[
            "Interest is assessed at each statement close (closing_day) at APR/12.",
            "The monthly payment is applied on the due day (statement_day).",
            "No grace period: the new purchase accrues interest from the first cycle.",
            "Extra cost is total currency paid with the purchase minus without it.",
        ],
    )


@lru_cache(maxsize=1)
def build_extraction_prompt() -> str:
    """Return the product-extraction prompt from ``prompts/``."""
    return (PROMPTS_DIR / "product_extraction_prompt.md").read_text(encoding="utf-8").strip()


def _coerce_price(value: object) -> float | None:
    """Turn a model value into a 2dp price, or None when it can't be read."""
    if value is None:
        return None
    try:
        return _round(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _coerce_confidence(value: object) -> float | None:
    """Turn a model value into a 0-1 confidence, or None."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def parse_extraction_payload(
    payload: dict[str, object], *, model: str | None = None
) -> ExtractResponse:
    """Validate the raw JSON object Gemini returned into an `ExtractResponse`."""
    return ExtractResponse(
        product_name=(payload.get("product_name") or None),  # type: ignore[arg-type]
        price=_coerce_price(payload.get("price")),
        currency=(payload.get("currency") or None),  # type: ignore[arg-type]
        raw_text=(payload.get("raw_text") or None),  # type: ignore[arg-type]
        confidence=_coerce_confidence(payload.get("confidence")),
        model=model,
    )


def extract_product(
    gemini: GeminiClient, *, image_bytes: bytes, mime_type: str
) -> ExtractResponse:
    """Ask Gemini to read a product name and price out of an image."""
    prompt = build_extraction_prompt()
    payload = gemini.extract_json(
        image_bytes=image_bytes, mime_type=mime_type, prompt=prompt
    )
    return parse_extraction_payload(payload, model=getattr(gemini, "model", None))


def list_purchase_plans(client: Client, *, user_id: str) -> list[PurchasePlanRead]:
    """Return every stored purchase plan for `user_id`."""
    rows = repository.list_purchase_plans(client, user_id=user_id)
    return [PurchasePlanRead.model_validate(row) for row in rows]


def record_purchase_plan(
    client: Client, *, user_id: str, payload: PurchasePlanCreate
) -> PurchasePlanRead:
    """Store a confirmed purchase and set it as the card's current monthly payment."""
    data = payload.model_dump()
    row = repository.insert_purchase_plan(client, user_id=user_id, payload=data)
    repository.upsert_monthly_payment(
        client,
        user_id=user_id,
        card_id=payload.card_id,
        monthly_payment=payload.monthly_payment,
    )
    return PurchasePlanRead.model_validate(row)


def delete_purchase_plan(client: Client, *, user_id: str, plan_id: str) -> None:
    """Delete one of the user's planned purchases, or raise NotFoundError."""
    if not repository.delete_purchase_plan(client, user_id=user_id, plan_id=plan_id):
        raise NotFoundError("No purchase plan with that id belongs to this user.")


def get_monthly_payment(
    client: Client, *, user_id: str, card_id: str
) -> MonthlyPaymentRead:
    """Return the card's stored monthly payment, or raise NotFoundError."""
    row = repository.get_monthly_payment(client, user_id=user_id, card_id=card_id)
    if row is None:
        raise NotFoundError("No monthly payment is stored for this card yet.")
    return MonthlyPaymentRead.model_validate(row)


def set_monthly_payment(
    client: Client, *, user_id: str, card_id: str, monthly_payment: float
) -> MonthlyPaymentRead:
    """Store (insert or update) the card's current monthly payment."""
    row = repository.upsert_monthly_payment(
        client, user_id=user_id, card_id=card_id, monthly_payment=monthly_payment
    )
    return MonthlyPaymentRead.model_validate(row)
