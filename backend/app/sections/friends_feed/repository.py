"""Supabase access for the Friends Feed section.

Owns one table (see `schema.sql` next to this file):

- ``friends_feed_entries`` — one row per feed event: the user's own finished
  lesson / refresh round (``actor`` = 'You') **and** the activity of their friends
  (``actor`` = the friend's name), written once by ``seed.py``. Append-only.

The backend uses the service-role client (no JWT auth yet) and passes an explicit
``user_id``; ``TODO(friends_feed)``: switch to ``get_supabase`` + RLS once auth
exists.
"""

from typing import Any

from supabase import Client

ENTRIES_TABLE = "friends_feed_entries"


def insert_entry(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Record one feed entry for a user and return the stored row."""
    row = {"user_id": user_id, **payload}
    response = client.table(ENTRIES_TABLE).insert(row).execute()
    rows = response.data or []
    return rows[0] if rows else row


def insert_entries(
    client: Client, *, user_id: str, payloads: list[dict[str, Any]]
) -> int:
    """Record several entries for one user in a single request; return the count."""
    if not payloads:
        return 0
    rows = [{"user_id": user_id, **payload} for payload in payloads]
    response = client.table(ENTRIES_TABLE).insert(rows).execute()
    return len(response.data or rows)


def list_entries(client: Client, *, user_id: str, limit: int) -> list[dict[str, Any]]:
    """Return the user's newest entries first, at most ``limit`` of them."""
    response = (
        client.table(ENTRIES_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def delete_entries_from_others(client: Client, *, user_id: str, self_actor: str) -> int:
    """Delete every friend (non-self) entry for a user; return how many were removed.

    Used by ``seed.py`` before it writes a fresh set, so re-running never
    duplicates activity. The user's own history is left alone.
    """
    response = (
        client.table(ENTRIES_TABLE)
        .delete()
        .eq("user_id", user_id)
        .neq("actor", self_actor)
        .execute()
    )
    return len(response.data or [])

