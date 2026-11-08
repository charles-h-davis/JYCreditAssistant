"""Business logic for the Notifications section.

One pure rule set decides whether a transaction looks like a planned purchase:

- **same card** — a plan and the transaction that settles it belong to one card;
- **same amount** — equal to the penny (both columns are ``numeric(12,2)``);
- **a purchase** — plaid's convention is that positive amounts leave the account,
  so refunds and payments never match;
- **on or after the plan date** — the date the plan was created, so history from
  before the user planned the purchase is ignored;
- **not dismissed** — the ``(plan, transaction)`` pair was not answered with ✗.
"""

from datetime import UTC, date, datetime
from typing import Any

from supabase import Client

from app.sections.notifications import repository
from app.sections.notifications.schemas import (
    DismissalCreate,
    DismissalRead,
    NotificationsFeed,
    PurchaseMatch,
)

#: Two `numeric(12,2)` amounts are the same when they differ by less than half a penny.
PRICE_TOLERANCE = 0.005


def _as_date(value: Any) -> date | None:
    """Parse a date column (`YYYY-MM-DD`) or a timestamp into a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return None


def _as_datetime(value: Any) -> datetime:
    """Parse a PostgREST timestamp into an aware UTC datetime."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(UTC)
    else:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _amount(value: Any) -> float:
    """Read a numeric column (Plaid amounts arrive as strings or Decimals)."""
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def dismissed_pairs(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    """The `(plan_id, transaction_id)` pairs the user has already answered."""
    return {
        (str(row.get("plan_id", "")), str(row.get("transaction_id", "")))
        for row in rows
    }


def find_matches(
    plans: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    *,
    dismissed: set[tuple[str, str]] | None = None,
) -> list[PurchaseMatch]:
    """Pair planned purchases with card transactions that look like their settlement."""
    answered = dismissed or set()
    matches: list[PurchaseMatch] = []

    for plan in plans:
        plan_id = str(plan.get("id", ""))
        planned_at = _as_datetime(plan.get("created_at"))
        planned_on = planned_at.date()
        planned_amount = _amount(plan.get("purchase_amount"))
        if not plan_id or planned_amount <= 0:
            continue

        for transaction in transactions:
            transaction_id = str(transaction.get("id", ""))
            if not transaction_id:
                continue
            if str(transaction.get("card_id", "")) != str(plan.get("card_id", "")):
                continue

            amount = _amount(transaction.get("amount"))
            if amount <= 0 or abs(amount - planned_amount) >= PRICE_TOLERANCE:
                continue

            happened_on = _as_date(transaction.get("authorized_date")) or _as_date(
                transaction.get("posted_date")
            )
            if happened_on is None or happened_on < planned_on:
                continue
            if (plan_id, transaction_id) in answered:
                continue

            matches.append(
                PurchaseMatch(
                    id=f"{plan_id}:{transaction_id}",
                    plan_id=plan_id,
                    transaction_id=transaction_id,
                    card_id=str(plan.get("card_id", "")),
                    product_name=plan.get("product_name"),
                    amount=planned_amount,
                    merchant_name=transaction.get("merchant_name")
                    or transaction.get("description"),
                    transaction_date=happened_on,
                    planned_at=planned_at,
                )
            )

    matches.sort(key=lambda match: (match.transaction_date, match.planned_at), reverse=True)
    return matches


def get_notifications(client: Client, *, user_id: str) -> NotificationsFeed:
    """Return every unread match for the bell: the count and the matches."""
    plans = repository.list_purchase_plans(client, user_id=user_id)
    transactions = repository.list_transactions(client, user_id=user_id)
    dismissed = dismissed_pairs(repository.list_dismissals(client, user_id=user_id))
    matches = find_matches(plans, transactions, dismissed=dismissed)
    return NotificationsFeed(count=len(matches), matches=matches)


def dismiss(client: Client, *, request: DismissalCreate) -> DismissalRead:
    """Remember that the user said ✗ to one match, so it never notifies again."""
    row = repository.insert_dismissal(
        client,
        user_id=request.user_id,
        payload={"plan_id": request.plan_id, "transaction_id": request.transaction_id},
    )
    return DismissalRead(
        id=str(row.get("id", "")),
        user_id=str(row.get("user_id", request.user_id)),
        plan_id=str(row.get("plan_id", request.plan_id)),
        transaction_id=str(row.get("transaction_id", request.transaction_id)),
        created_at=row.get("created_at"),
    )
