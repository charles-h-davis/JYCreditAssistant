"""Supabase access for the Card Storage section.

Tables (see `schema.sql` next to this file):

- ``plaid_items``      one row per linked Plaid Item (holds the access token).
- ``credit_cards``     one row per card, manual or loaded from Plaid.
- ``card_transactions`` Plaid transaction history, keyed by transaction id.

Every function takes the Supabase client and an explicit ``user_id``: the API has
no auth dependency yet, so the router injects the service-role client and we
filter ownership by hand. ``TODO(card_storage)``: switch to ``get_supabase`` with
a JWT-derived user id once auth exists, and let RLS enforce ownership.

Upserts use the natural keys from `schema.sql` so re-running a sync never
duplicates rows: ``plaid_items.item_id``, ``(credit_cards.user_id,
credit_cards.plaid_account_id)`` and ``card_transactions.plaid_transaction_id``.
"""

from typing import Any

from supabase import Client

CARDS_TABLE = "credit_cards"
PLAID_ITEMS_TABLE = "plaid_items"
TRANSACTIONS_TABLE = "card_transactions"


# --- cards -----------------------------------------------------------------


def list_cards(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return all card rows for `user_id`, oldest first."""
    response = (
        client.table(CARDS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return response.data or []


def get_card(client: Client, *, user_id: str, card_id: str) -> dict[str, Any] | None:
    """Return one card row owned by `user_id`, or None."""
    response = (
        client.table(CARDS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("id", card_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def insert_card(client: Client, *, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Insert one card row for `user_id` and return the created row."""
    row = {"user_id": user_id, **payload}
    response = client.table(CARDS_TABLE).insert(row).execute()
    rows = response.data or []
    return rows[0] if rows else row


def upsert_cards(
    client: Client, *, user_id: str, payloads: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Upsert Plaid-loaded cards, keyed on `(user_id, plaid_account_id)`."""
    if not payloads:
        return []
    rows = [{"user_id": user_id, **payload} for payload in payloads]
    response = (
        client.table(CARDS_TABLE)
        .upsert(rows, on_conflict="user_id,plaid_account_id")
        .execute()
    )
    return response.data or rows


def delete_card(client: Client, *, user_id: str, card_id: str) -> None:
    """Delete one card row owned by `user_id` (transactions cascade)."""
    client.table(CARDS_TABLE).delete().eq("user_id", user_id).eq("id", card_id).execute()


# --- plaid items -----------------------------------------------------------


def get_plaid_item(
    client: Client, *, user_id: str, item_id: str
) -> dict[str, Any] | None:
    """Return the stored Plaid Item row for `user_id`, or None."""
    response = (
        client.table(PLAID_ITEMS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("item_id", item_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def upsert_plaid_item(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert/update a Plaid Item (access token + institution), keyed on `item_id`."""
    row = {"user_id": user_id, **payload}
    response = client.table(PLAID_ITEMS_TABLE).upsert(row, on_conflict="item_id").execute()
    rows = response.data or []
    return rows[0] if rows else row


def update_plaid_item_cursor(
    client: Client, *, user_id: str, item_id: str, cursor: str | None
) -> None:
    """Store the latest `/transactions/sync` cursor for the next incremental sync."""
    if not cursor:
        return
    (
        client.table(PLAID_ITEMS_TABLE)
        .update({"transactions_cursor": cursor})
        .eq("user_id", user_id)
        .eq("item_id", item_id)
        .execute()
    )


# --- transactions ----------------------------------------------------------


def list_transactions(
    client: Client, *, user_id: str, card_id: str
) -> list[dict[str, Any]]:
    """Return one card's transactions, newest first."""
    response = (
        client.table(TRANSACTIONS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("card_id", card_id)
        .order("posted_date", desc=True)
        .execute()
    )
    return response.data or []


def upsert_transactions(
    client: Client, *, user_id: str, card_id: str, payloads: list[dict[str, Any]]
) -> int:
    """Upsert transactions for `card_id`, keyed on `plaid_transaction_id`."""
    if not payloads:
        return 0
    rows = [{"user_id": user_id, "card_id": card_id, **payload} for payload in payloads]
    response = (
        client.table(TRANSACTIONS_TABLE)
        .upsert(rows, on_conflict="plaid_transaction_id")
        .execute()
    )
    return len(response.data or rows)


def delete_transactions_by_plaid_ids(
    client: Client, *, user_id: str, plaid_transaction_ids: list[str]
) -> int:
    """Delete transactions the issuer removed, returning how many rows went away."""
    if not plaid_transaction_ids:
        return 0
    response = (
        client.table(TRANSACTIONS_TABLE)
        .delete()
        .eq("user_id", user_id)
        .in_("plaid_transaction_id", plaid_transaction_ids)
        .execute()
    )
    return len(response.data or [])
