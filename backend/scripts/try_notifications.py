#!/usr/bin/env python3
"""End-to-end manual test for the Notifications section.

Exercises both answers against a locally running API and the real database, and
cleans up every row it creates:

  ✓ accept — plan a purchase, insert a matching transaction, see the match, then
             delete the plan through the Cost to Buy API: the match disappears.
  ✗ dismiss — plan a second purchase, insert a matching transaction, see the match,
             POST a dismissal: the match disappears and the plan is still there.

Usage (from backend/):
    ../.venv/Scripts/python.exe scripts/try_notifications.py [user-id]

Requirements:
  - The API running on http://127.0.0.1:8000, started from backend/.
  - card_storage, cost_to_buy and notifications schemas applied.
  - `httpx` + the app package (for the throwaway transaction rows).
"""

import os
import sys
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from supabase import Client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import get_supabase_admin  # noqa: E402
from app.sections.friends.seed import resolve_user_id  # noqa: E402

API = os.environ.get("CREDITMATE_API", "http://127.0.0.1:8000")
NOTIFICATIONS_URL = f"{API}/api/v1/notifications"
PLANS_URL = f"{API}/api/v1/cost-to-buy/purchase-plans"
CARDS_URL = f"{API}/api/v1/card-storage/cards"

#: Deliberately odd prices so they cannot collide with seeded data.
ACCEPT_PRICE = 137.42
DISMISS_PRICE = 249.17
MERCHANT = "Demo Store"


def first_card(client: httpx.Client, user_id: str) -> dict[str, Any]:
    """Return the user's first card (the demo account has several)."""
    response = client.get(CARDS_URL, params={"user_id": user_id})
    if response.status_code != 200:
        sys.exit(f"GET /cards failed ({response.status_code}): {response.text}")
    cards = response.json()
    if not cards:
        sys.exit("No cards on the demo account — run scripts/seed_demo.py first.")
    return cards[0]


def create_plan(
    client: httpx.Client, *, user_id: str, card_id: str, price: float, name: str
) -> str:
    """Plan a purchase the way the Check-a-Purchase flow does."""
    response = client.post(
        PLANS_URL,
        json={
            "user_id": user_id,
            "card_id": card_id,
            "product_name": name,
            "purchase_amount": price,
            "monthly_payment": 25,
        },
    )
    if response.status_code != 201:
        sys.exit(f"POST /purchase-plans failed ({response.status_code}): {response.text}")
    return str(response.json()["id"])


def insert_transaction(db: Client, *, user_id: str, card_id: str, price: float) -> str:
    """Write the 'the user just paid' row the demo inserts by hand."""
    row = {
        "user_id": user_id,
        "card_id": card_id,
        "plaid_transaction_id": f"demo-notification-{uuid4()}",
        "description": f"{MERCHANT.upper()} LTD",
        "merchant_name": MERCHANT,
        "amount": price,
        "category": "Shops",
        "authorized_date": date.today().isoformat(),
        "pending": False,
        "iso_currency_code": "GBP",
    }
    created = db.table("card_transactions").insert(row).execute().data or []
    if not created:
        sys.exit("Could not insert the demo transaction.")
    return str(created[0]["id"])


def match_for(client: httpx.Client, user_id: str, plan_id: str) -> dict[str, Any] | None:
    """Return the notification for one plan, or None when it is not reported."""
    response = client.get(NOTIFICATIONS_URL, params={"user_id": user_id})
    if response.status_code != 200:
        sys.exit(f"GET /notifications failed ({response.status_code}): {response.text}")
    body = response.json()
    return next(
        (match for match in body["matches"] if match["plan_id"] == plan_id), None
    )


def main() -> int:
    db = get_supabase_admin()
    user_id = sys.argv[1] if len(sys.argv) > 1 else resolve_user_id(db)
    card_id = ""
    plans: list[str] = []
    transactions: list[str] = []
    dismissed_plans: list[str] = []

    try:
        with httpx.Client(timeout=30) as client:
            if client.get(f"{API}/health").status_code != 200:
                sys.exit(f"The API is not answering on {API} — start it from backend/.")

            card = first_card(client, user_id)
            card_id = str(card["id"])
            print(f"card: {card['nickname']} ({card_id})")

            # --- the tick: deleting the plan is the answer --------------------
            accept_plan = create_plan(
                client,
                user_id=user_id,
                card_id=card_id,
                price=ACCEPT_PRICE,
                name="Accept-path demo item",
            )
            plans.append(accept_plan)
            transactions.append(
                insert_transaction(
                    db, user_id=user_id, card_id=card_id, price=ACCEPT_PRICE
                )
            )

            match = match_for(client, user_id, accept_plan)
            if match is None:
                sys.exit("FAILED: the matching transaction was not reported")
            print(f"matched (accept path): {match['product_name']} {match['amount']}")

            deleted = client.delete(f"{PLANS_URL}/{accept_plan}", params={"user_id": user_id})
            if deleted.status_code != 204:
                sys.exit(f"DELETE /purchase-plans failed ({deleted.status_code})")
            plans.remove(accept_plan)
            if match_for(client, user_id, accept_plan) is not None:
                sys.exit("FAILED: the match survived the plan being deleted")
            print("tick path OK — plan deleted, notification gone")

            # --- the cross: keep the plan, silence the pair -------------------
            dismiss_plan = create_plan(
                client,
                user_id=user_id,
                card_id=card_id,
                price=DISMISS_PRICE,
                name="Dismiss-path demo item",
            )
            plans.append(dismiss_plan)
            transactions.append(
                insert_transaction(
                    db, user_id=user_id, card_id=card_id, price=DISMISS_PRICE
                )
            )

            match = match_for(client, user_id, dismiss_plan)
            if match is None:
                sys.exit("FAILED: the second matching transaction was not reported")

            dismissed = client.post(
                f"{NOTIFICATIONS_URL}/dismissals",
                json={
                    "user_id": user_id,
                    "plan_id": match["plan_id"],
                    "transaction_id": match["transaction_id"],
                },
            )
            if dismissed.status_code != 201:
                sys.exit(
                    f"POST /dismissals failed ({dismissed.status_code}): {dismissed.text}"
                )
            dismissed_plans.append(match["plan_id"])
            if match_for(client, user_id, dismiss_plan) is not None:
                sys.exit("FAILED: the dismissed match is still being reported")

            remaining = client.get(PLANS_URL, params={"user_id": user_id}).json()
            if not any(plan["id"] == dismiss_plan for plan in remaining):
                sys.exit("FAILED: the cross should not delete the planned purchase")
            print("cross path OK — plan kept, notification silenced")

    finally:
        with httpx.Client(timeout=30) as client:
            for plan_id in plans:
                client.delete(f"{PLANS_URL}/{plan_id}", params={"user_id": user_id})
        if transactions:
            db.table("card_transactions").delete().in_("id", transactions).execute()
        if dismissed_plans:
            # Only the dismissals this run created — never the user's own answers.
            db.table("purchase_match_dismissals").delete().in_(
                "plan_id", dismissed_plans
            ).execute()
        print("cleaned up the demo plans, transactions and dismissals")

    print("\nOK — matching, ticking and crossing all behave.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

