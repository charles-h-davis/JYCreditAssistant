"""Supabase access for the Cost to Buy section.

Tables (see ``schema.sql`` next to this file):

- ``purchase_plans``       confirmed purchases (one row per purchase).
- ``card_payment_settings`` the current monthly payment per (user, card).

Every function takes the Supabase client and an explicit ``user_id``: the API has
no auth dependency yet, so the router injects the service-role client and we
filter ownership by hand. ``TODO(cost_to_buy)``: switch to ``get_supabase`` with a
JWT-derived user id once auth exists, and let RLS enforce ownership.
"""

from typing import Any

from supabase import Client

PURCHASE_PLANS_TABLE = "purchase_plans"
PAYMENT_SETTINGS_TABLE = "card_payment_settings"


def list_purchase_plans(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return all purchase plans for `user_id`, newest first."""
    response = (
        client.table(PURCHASE_PLANS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def insert_purchase_plan(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert one purchase plan for `user_id` and return the created row."""
    row = {"user_id": user_id, **payload}
    response = client.table(PURCHASE_PLANS_TABLE).insert(row).execute()
    rows = response.data or []
    return rows[0] if rows else row


def get_monthly_payment(
    client: Client, *, user_id: str, card_id: str
) -> dict[str, Any] | None:
    """Return the stored monthly-payment row for one card, or None."""
    response = (
        client.table(PAYMENT_SETTINGS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("card_id", card_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def upsert_monthly_payment(
    client: Client, *, user_id: str, card_id: str, monthly_payment: float
) -> dict[str, Any]:
    """Insert/update the current monthly payment, keyed on `(user_id, card_id)`."""
    row = {"user_id": user_id, "card_id": card_id, "monthly_payment": monthly_payment}
    response = (
        client.table(PAYMENT_SETTINGS_TABLE)
        .upsert(row, on_conflict="user_id,card_id")
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else row
