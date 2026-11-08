"""Supabase access for the Notifications section.

Owns one table (see `schema.sql` next to this file):

- ``purchase_match_dismissals`` — ``(user_id, plan_id, transaction_id)`` pairs the
  user said "no" to, so the same match never notifies twice.

Reads — but never writes — two tables owned by other sections, always filtered by
``user_id``: ``purchase_plans`` (cost_to_buy) and ``card_transactions``
(card_storage). Accepting a match deletes the plan through the Cost to Buy API.

The backend uses the service-role client (no JWT auth yet); ``TODO(notifications)``:
switch to ``get_supabase`` + RLS once auth exists.
"""

from typing import Any

from supabase import Client

PURCHASE_PLANS_TABLE = "purchase_plans"
TRANSACTIONS_TABLE = "card_transactions"
DISMISSALS_TABLE = "purchase_match_dismissals"


def list_purchase_plans(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return the user's planned purchases, newest first."""
    response = (
        client.table(PURCHASE_PLANS_TABLE)
        .select("id,user_id,card_id,product_name,purchase_amount,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def list_transactions(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return the user's card transactions, newest first."""
    response = (
        client.table(TRANSACTIONS_TABLE)
        .select(
            "id,user_id,card_id,amount,description,merchant_name,"
            "authorized_date,posted_date,pending"
        )
        .eq("user_id", user_id)
        .order("posted_date", desc=True)
        .execute()
    )
    return response.data or []


def list_dismissals(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return every dismissal the user has recorded."""
    response = (
        client.table(DISMISSALS_TABLE)
        .select("plan_id,transaction_id")
        .eq("user_id", user_id)
        .execute()
    )
    return response.data or []


def insert_dismissal(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Record one dismissal, keyed on `(user_id, plan_id, transaction_id)`."""
    row = {"user_id": user_id, **payload}
    response = (
        client.table(DISMISSALS_TABLE)
        .upsert(row, on_conflict="user_id,plan_id,transaction_id")
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else row
