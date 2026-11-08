"""Seed a realistic demo account so the frontend has something to show.

Idempotent: every run resets *only the demo user's* rows (cards, transactions,
purchase plans, payment settings, learning progress, friends, friends-feed
entries) and re-creates them, so the demo is reproducible right before a
presentation.
Run from `backend/` after both `schema.sql` files and the credit-learning seed:

    ..\\.venv\\Scripts\\python.exe scripts\\seed_demo.py

Demo login: demo@demo.com / demo123!
"""

import logging
import random
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supabase import Client  # noqa: E402

from app.core.database import get_supabase_admin  # noqa: E402
from app.sections.friends import seed as friends_seed  # noqa: E402
from app.sections.friends_feed import seed as feed_seed  # noqa: E402

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@demo.com"
DEMO_PASSWORD = "demo123!"
DEMO_DISPLAY_NAME = "Alex Morgan"
DEMO_FIRST_NAME = "Alex"

#: Synthetic Plaid transaction ids are prefixed so they are easy to spot/clean up.
TX_PREFIX = "demo-seed-"

#: One entry per card. `weight` scales how many transactions the card gets.
CARDS: list[dict[str, Any]] = [
    {
        "nickname": "Classic Card",
        "issuer": "Chase",
        "last_four": "4821",
        "credit_limit": 6000.00,
        # Target closing balance. The seed derives the opening balance from this
        # and the generated transactions, so the row always reconciles with the
        # history the user can see.
        "target_balance": 3000.00,
        "purchase_apr": 34.9,
        "closing_day": 23,
        "statement_day": 18,
        "monthly_payment": 300.0,
        "daily": (0.10, 0.35, 0.35, 0.20),
    },
    {
        "nickname": "Capital One Credit",
        "issuer": "Capital One",
        "last_four": "9032",
        "credit_limit": 2500.00,
        "target_balance": 1120.00,
        "purchase_apr": 29.9,
        "closing_day": 12,
        "statement_day": 5,
        "monthly_payment": 110.0,
        "daily": (0.50, 0.40, 0.09, 0.01),
    },
    {
        "nickname": "Rewards Card",
        "issuer": "American Express",
        "last_four": "7710",
        "credit_limit": 4000.00,
        "target_balance": 620.00,
        "purchase_apr": 22.9,
        "closing_day": 28,
        "statement_day": 22,
        "monthly_payment": 60.0,
        "daily": (0.62, 0.31, 0.06, 0.01),
    },
]

#: (merchant, Plaid personal_finance_category, min amount, max amount)
MERCHANTS: list[tuple[str, str, float, float]] = [
    ("Tesco", "FOOD_AND_DRINK", 18.0, 78.0),
    ("ASDA", "FOOD_AND_DRINK", 15.0, 70.0),
    ("Sainsbury's", "FOOD_AND_DRINK", 12.0, 55.0),
    ("Aldi", "FOOD_AND_DRINK", 9.0, 48.0),
    ("Pret A Manger", "FOOD_AND_DRINK", 3.5, 12.0),
    ("Costa Coffee", "FOOD_AND_DRINK", 2.5, 9.0),
    ("Deliveroo", "FOOD_AND_DRINK", 14.0, 38.0),
    ("Nando's", "FOOD_AND_DRINK", 18.0, 46.0),
    ("TfL Travel Charge", "TRANSPORTATION", 6.0, 26.0),
    ("Uber", "TRANSPORTATION", 8.0, 32.0),
    ("Trainline", "TRANSPORTATION", 18.0, 64.0),
    ("Shell", "TRANSPORTATION", 32.0, 68.0),
    ("H&M", "GENERAL_MERCHANDISE", 24.0, 96.0),
    ("Zara", "GENERAL_MERCHANDISE", 28.0, 88.0),
    ("Amazon", "GENERAL_MERCHANDISE", 12.0, 74.0),
    ("Nike", "GENERAL_MERCHANDISE", 45.0, 120.0),
    ("Boots", "PERSONAL_CARE", 8.0, 34.0),
    ("PureGym", "PERSONAL_CARE", 22.0, 28.0),
    ("Netflix", "ENTERTAINMENT", 10.0, 12.0),
    ("Spotify", "ENTERTAINMENT", 11.0, 12.0),
    ("Odeon Cinema", "ENTERTAINMENT", 9.0, 22.0),
    ("Vodafone", "RENT_AND_UTILITIES", 22.0, 42.0),
    ("British Gas", "RENT_AND_UTILITIES", 55.0, 92.0),
]

PAYMENT_DESCRIPTION = "Payment received - thank you"
PAYMENT_CATEGORY = "LOAN_PAYMENTS"

#: (card index, days ago, amount) — every card gets a payment in each month of
#: history, and the Classic Card's land inside the last 30 days so its dashboard
#: balance chart visibly falls towards today.
PAYMENTS: list[tuple[int, int, float]] = [
    (0, 45, 800.00),
    (0, 22, 1400.00),
    (0, 5, 1100.00),
    (1, 40, 300.00),
    (1, 5, 420.00),
    (2, 35, 150.00),
    (2, 4, 180.00),
]

#: Planned purchases shown on the "Check a purchase" screen.
PURCHASE_PLANS: list[dict[str, Any]] = [
    {
        "product_name": "Carrera Mountain Bike",
        "purchase_amount": 128.32,
        "monthly_payment": 300.0,
        "months_to_payoff": 13,
        "total_interest": 22.41,
    },
    {
        "product_name": "H&M Black Suit",
        "purchase_amount": 99.99,
        "monthly_payment": 300.0,
        "months_to_payoff": 13,
        "total_interest": 15.87,
    },
]

#: Completed lessons for the demo user: the first category fully done, the second
#: one lesson in, so the roadmap shows both a finished and a partial activity.
COMPLETED_LESSONS = 4
CURRENT_STREAK = 4
LONGEST_STREAK = 7


# ---------------------------------------------------------------------------
# Auth user
# ---------------------------------------------------------------------------


def _iter_users(client: Client) -> list[Any]:
    """Return every auth user (the admin API paginates at 50 per page)."""
    users: list[Any] = []
    for page in range(1, 21):
        batch = client.auth.admin.list_users(page=page, per_page=50)
        if not batch:
            break
        users.extend(batch)
        if len(batch) < 50:
            break
    return users


def ensure_demo_user(client: Client) -> str:
    """Create the demo auth user if needed, then force its password. Returns the id."""
    for user in _iter_users(client):
        if (user.email or "").lower() == DEMO_EMAIL:
            client.auth.admin.update_user_by_id(
                user.id,
                {
                    "password": DEMO_PASSWORD,
                    "email_confirm": True,
                    "user_metadata": {
                        "display_name": DEMO_DISPLAY_NAME,
                        "first_name": DEMO_FIRST_NAME,
                    },
                },
            )
            logger.info("Updated existing demo user %s (%s)", DEMO_EMAIL, user.id)
            return str(user.id)

    created = client.auth.admin.create_user(
        {
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "email_confirm": True,
            "user_metadata": {
                "display_name": DEMO_DISPLAY_NAME,
                "first_name": DEMO_FIRST_NAME,
            },
        }
    )
    user_id = str(getattr(created, "id", None) or getattr(created, "user", None).id)
    logger.info("Created demo user %s (%s)", DEMO_EMAIL, user_id)
    return user_id


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------


def _clear_demo_rows(client: Client, user_id: str) -> None:
    """Delete the demo user's own data so re-runs stay deterministic."""
    for table in (
        "purchase_plans",
        "card_payment_settings",
        "card_transactions",
        "credit_cards",
        "learning_completions",
        "learning_attempts",
        "learning_streaks",
        "friends",
        "friends_feed_entries",
    ):
        try:
            client.table(table).delete().eq("user_id", user_id).execute()
        except Exception as exc:  # noqa: BLE001 - optional sections may be unseeded
            logger.warning("Could not clear %s: %s", table, str(exc)[:160])


def _money(value: float) -> float:
    """Round money to two decimals."""
    return round(value, 2)


def _transactions_for_card(
    card_index: int, today: date, rng: random.Random
) -> list[dict[str, Any]]:
    """Build ~2 months of daily spending plus that card's monthly payments."""
    rows: list[dict[str, Any]] = []
    weights = CARDS[card_index]["daily"]
    recent: list[str] = []
    for days_ago in range(56, -1, -1):
        day = today - timedelta(days=days_ago)
        count = rng.choices((0, 1, 2, 3), weights=weights, k=1)[0]
        for _ in range(count):
            # Avoid the same merchant three days running — it reads as a bug.
            merchant, category, low, high = rng.choice(MERCHANTS)
            for _attempt in range(6):
                if merchant not in recent[-3:]:
                    break
                merchant, category, low, high = rng.choice(MERCHANTS)
            recent.append(merchant)
            amount = _money(rng.uniform(low, high))
            rows.append(
                {
                    "plaid_transaction_id": f"{TX_PREFIX}{uuid4().hex}",
                    "description": merchant.upper(),
                    "merchant_name": merchant,
                    "amount": amount,
                    "category": category,
                    "authorized_date": day.isoformat(),
                    "posted_date": (day + timedelta(days=1)).isoformat(),
                    "pending": False,
                    "iso_currency_code": "GBP",
                }
            )
    for index, days_ago, amount in PAYMENTS:
        if index != card_index:
            continue
        day = today - timedelta(days=days_ago)
        rows.append(
            {
                "plaid_transaction_id": f"{TX_PREFIX}{uuid4().hex}",
                "description": PAYMENT_DESCRIPTION.upper(),
                "merchant_name": "Payment - thank you",
                "amount": -amount,
                "category": PAYMENT_CATEGORY,
                "authorized_date": day.isoformat(),
                "posted_date": (day + timedelta(days=1)).isoformat(),
                "pending": False,
                "iso_currency_code": "GBP",
            }
        )
    return rows


#: Shown when the Cost to Buy tables have not been created yet.
MISSING_COST_TO_BUY = (
    "Table not found: run backend/app/sections/cost_to_buy/schema.sql in the "
    "Supabase SQL editor (Dashboard -> SQL Editor -> New query -> Run)."
)


def _insert_chunked(
    client: Client, table: str, rows: list[dict[str, Any]], size: int = 100
) -> int:
    """Insert rows in batches; return how many were written."""
    written = 0
    for start in range(0, len(rows), size):
        batch = rows[start : start + size]
        response = client.table(table).insert(batch).execute()
        written += len(response.data or batch)
    return written


def build_history(today: date, rng: random.Random) -> list[dict[str, Any]]:
    """Generate each card's transactions and derive its opening/closing balance.

    The balance is never typed by hand: ``closing = opening + sum(transactions)``,
    so the card row always reconciles with the history the UI shows.
    """
    plans: list[dict[str, Any]] = []
    for index, spec in enumerate(CARDS):
        rows = _transactions_for_card(index, today, rng)
        net = _money(sum(row["amount"] for row in rows))
        # `target_balance` is a floor: the opening balance makes up the difference,
        # and can be zero when spending alone already exceeds the target.
        opening = _money(max(0.0, float(spec["target_balance"]) - net))
        current = _money(opening + net)
        if current > float(spec["credit_limit"]):
            raise RuntimeError(
                f"{spec['nickname']}: derived balance {current:.2f} exceeds the "
                f"credit limit {spec['credit_limit']:.2f}."
            )
        plans.append(
            {
                **spec,
                "transactions": rows,
                "net": net,
                "opening_balance": opening,
                "current_balance": current,
            }
        )
    return plans


def seed_cards(
    client: Client, user_id: str, plans: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Insert the demo cards with balances derived from their transaction history."""
    rows = [
        {
            "user_id": user_id,
            "nickname": plan["nickname"],
            "issuer": plan["issuer"],
            "last_four": plan["last_four"],
            "credit_limit": plan["credit_limit"],
            "current_balance": plan["current_balance"],
            "available_balance": _money(plan["credit_limit"] - plan["current_balance"]),
            "purchase_apr": plan["purchase_apr"],
            "closing_day": plan["closing_day"],
            "statement_day": plan["statement_day"],
            "is_secured": False,
        }
        for plan in plans
    ]
    response = client.table("credit_cards").insert(rows).execute()
    return response.data or []


def seed_transactions(
    client: Client,
    user_id: str,
    cards: list[dict[str, Any]],
    plans: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Insert the pre-built two-month transaction history for every card."""
    all_rows: list[dict[str, Any]] = []
    for index, card in enumerate(cards):
        for row in plans[index]["transactions"]:
            all_rows.append({"user_id": user_id, "card_id": card["id"], **row})
    _insert_chunked(client, "card_transactions", all_rows)
    return all_rows


def seed_payment_settings(
    client: Client, user_id: str, cards: list[dict[str, Any]]
) -> int:
    """Store each card's current monthly repayment."""
    rows = [
        {
            "user_id": user_id,
            "card_id": card["id"],
            "monthly_payment": CARDS[index]["monthly_payment"],
        }
        for index, card in enumerate(cards)
    ]
    try:
        _insert_chunked(client, "card_payment_settings", rows)
    except Exception as exc:  # noqa: BLE001 - the table may not exist yet
        logger.warning("Skipped card_payment_settings (%s): %s", str(exc)[:80], MISSING_COST_TO_BUY)
        return 0
    return len(rows)


def seed_purchase_plans(
    client: Client, user_id: str, cards: list[dict[str, Any]]
) -> int:
    """Store two planned purchases against the first card."""
    if not cards:
        return 0
    rows = [
        {"user_id": user_id, "card_id": cards[0]["id"], **plan} for plan in PURCHASE_PLANS
    ]
    try:
        _insert_chunked(client, "purchase_plans", rows)
    except Exception as exc:  # noqa: BLE001 - the table may not exist yet
        logger.warning("Skipped purchase_plans (%s): %s", str(exc)[:80], MISSING_COST_TO_BUY)
        return 0
    return len(rows)


def seed_friends(client: Client, user_id: str) -> int:
    """Load the demo friends (the people the feed talks about)."""
    try:
        return friends_seed.run(client, user_id)
    except Exception as exc:  # noqa: BLE001 - the table may not exist yet
        logger.warning(
            "Skipped friends (%s): run app/sections/friends/schema.sql first.",
            str(exc)[:80],
        )
        return 0


def seed_friend_activity(client: Client, user_id: str) -> int:
    """Generate a few days of activity for the demo friends (the feed's content)."""
    try:
        return feed_seed.run(client, user_id)
    except Exception as exc:  # noqa: BLE001 - the table may not exist yet
        logger.warning(
            "Skipped friends feed (%s): run app/sections/friends_feed/schema.sql first.",
            str(exc)[:80],
        )
        return 0


def seed_learning(client: Client, user_id: str, today: date) -> dict[str, int]:
    """Complete the first few lessons and give the demo user an active streak."""
    categories = (
        client.table("learning_categories")
        .select("id,position")
        .order("position")
        .execute()
        .data
        or []
    )
    lessons: list[dict[str, Any]] = []
    for category in categories:
        rows = (
            client.table("learning_lessons")
            .select("id,slug,position")
            .eq("category_id", category["id"])
            .order("position")
            .execute()
            .data
            or []
        )
        lessons.extend(rows)

    if not lessons:
        logger.warning("No lessons found - run app.sections.credit_learning.seed first.")
        return {"completions": 0, "streak": 0}

    now = datetime.now(UTC)
    completions = []
    for index, lesson in enumerate(lessons[:COMPLETED_LESSONS]):
        completed_at = now - timedelta(days=COMPLETED_LESSONS - index)
        completions.append(
            {
                "user_id": user_id,
                "lesson_id": lesson["id"],
                "attempts": 1 + index % 2,
                "last_score": 4 + index % 2,
                "best_score": 5,
                "first_completed_at": completed_at.isoformat(),
                "last_completed_at": completed_at.isoformat(),
            }
        )
    _insert_chunked(client, "learning_completions", completions)

    client.table("learning_streaks").upsert(
        {
            "user_id": user_id,
            "current_streak": CURRENT_STREAK,
            "longest_streak": LONGEST_STREAK,
            "last_activity_date": today.isoformat(),
        },
        on_conflict="user_id",
    ).execute()
    return {"completions": len(completions), "streak": CURRENT_STREAK}


def run(client: Client | None = None) -> dict[str, int]:
    """Reset and re-seed the demo account; return the row counts written."""
    client = client or get_supabase_admin()
    today = date.today()
    rng = random.Random(20260711)

    user_id = ensure_demo_user(client)
    _clear_demo_rows(client, user_id)

    history = build_history(today, rng)
    cards = seed_cards(client, user_id, history)
    transactions = seed_transactions(client, user_id, cards, history)
    payments = seed_payment_settings(client, user_id, cards)
    plans = seed_purchase_plans(client, user_id, cards)
    learning = seed_learning(client, user_id, today)
    friends = seed_friends(client, user_id)
    friend_activity = seed_friend_activity(client, user_id)

    counts = {
        "cards": len(cards),
        "transactions": len(transactions),
        "payment_settings": payments,
        "purchase_plans": plans,
        "learning_completions": learning["completions"],
        "streak": learning["streak"],
        "friends": friends,
        "friend_activity": friend_activity,
    }
    logger.info("Demo account %s seeded: %s", DEMO_EMAIL, counts)

    # Prove the card rows reconcile with the history we just wrote.
    for card, plan in zip(cards, history, strict=False):
        stored = float(card["current_balance"])
        expected = _money(plan["opening_balance"] + plan["net"])
        logger.info(
            "%s: opening %.2f %+.2f transactions = %.2f balance (%d rows) %s",
            card["nickname"],
            plan["opening_balance"],
            plan["net"],
            stored,
            len(plan["transactions"]),
            "reconciled" if abs(stored - expected) < 0.005 else "MISMATCH",
        )
        if abs(stored - expected) >= 0.005:
            raise RuntimeError(
                f"{card['nickname']}: balance {stored:.2f} does not match "
                f"opening {plan['opening_balance']:.2f} + transactions {plan['net']:.2f}"
            )

    if cards:
        cutoff = today - timedelta(days=29)
        recent = [
            row["amount"]
            for row in transactions
            if row["card_id"] == cards[0]["id"]
            and date.fromisoformat(str(row["authorized_date"])) >= cutoff
        ]
        net_30d = _money(sum(recent))
        balance_now = float(cards[0]["current_balance"])
        logger.info(
            "Card 1 30-day window: %.2f now, %.2f thirty days ago (net %+.2f)",
            balance_now,
            balance_now - net_30d,
            net_30d,
        )
    return counts


def main() -> None:
    """Seed the demo account into the configured Supabase project."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()


if __name__ == "__main__":
    main()
