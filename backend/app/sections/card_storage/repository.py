"""Supabase access for the Card Storage section.

Table: `credit_cards` (TODO: create the migration in Supabase).

RLS policy must be `user_id = auth.uid()` for select/insert/update/delete, so the
anon client is safe here.
"""

from typing import Any

from supabase import Client

TABLE = "credit_cards"


def list_cards(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return all rows in `credit_cards` for `user_id`."""
    raise NotImplementedError(f"TODO(card_storage): implement list_cards on '{TABLE}'")


def insert_card(client: Client, *, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Insert one card row for `user_id` and return the created row."""
    raise NotImplementedError(f"TODO(card_storage): implement insert_card on '{TABLE}'")


def delete_card(client: Client, *, user_id: str, card_id: str) -> None:
    """Delete one card row owned by `user_id`."""
    raise NotImplementedError(f"TODO(card_storage): implement delete_card on '{TABLE}'")
