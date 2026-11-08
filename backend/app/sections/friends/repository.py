"""Supabase access for the Friends section.

Owns one table (see `schema.sql` next to this file):

- ``friends`` — one row per friend a user has added: ``friend_name``,
  ``friend_email``, unique on ``(user_id, friend_email)``.

The backend uses the service-role client (no JWT auth yet) and passes an explicit
``user_id``; ``TODO(friends)``: switch to ``get_supabase`` + RLS once auth exists.
"""

from typing import Any

from supabase import Client

FRIENDS_TABLE = "friends"


def list_friends(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return the user's friends, most recently added first."""
    response = (
        client.table(FRIENDS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_friend(client: Client, *, user_id: str, email: str) -> dict[str, Any] | None:
    """Return the row for one email in this user's list, or None."""
    response = (
        client.table(FRIENDS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("friend_email", email)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def insert_friend(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert one friend and return the stored row."""
    row = {"user_id": user_id, **payload}
    response = client.table(FRIENDS_TABLE).insert(row).execute()
    rows = response.data or []
    return rows[0] if rows else row


def upsert_friend(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert/update one friend, keyed on `(user_id, friend_email)` — used by the seed."""
    row = {"user_id": user_id, **payload}
    response = (
        client.table(FRIENDS_TABLE)
        .upsert(row, on_conflict="user_id,friend_email")
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else row


def delete_friend(client: Client, *, user_id: str, friend_id: str) -> list[dict[str, Any]]:
    """Delete one friend owned by the user and return the rows that were removed."""
    response = (
        client.table(FRIENDS_TABLE)
        .delete()
        .eq("user_id", user_id)
        .eq("id", friend_id)
        .execute()
    )
    return response.data or []
