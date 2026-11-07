"""Supabase access for the AI Credit Assistant section.

Tables: `chat_sessions` and `chat_messages` (TODO: create the migrations).

RLS must be `user_id = auth.uid()` on both tables — conversations contain personal
financial details.
"""

from typing import Any

from supabase import Client

SESSIONS_TABLE = "chat_sessions"
MESSAGES_TABLE = "chat_messages"


def get_or_create_session(
    client: Client, *, user_id: str, conversation_id: str | None
) -> dict[str, Any]:
    """Return the existing session or create one for `user_id`."""
    raise NotImplementedError(
        f"TODO(ai_assistant): implement get_or_create_session on '{SESSIONS_TABLE}'"
    )


def list_messages(client: Client, *, conversation_id: str) -> list[dict[str, Any]]:
    """Return the transcript of one conversation, oldest first."""
    raise NotImplementedError(f"TODO(ai_assistant): implement list_messages on '{MESSAGES_TABLE}'")


def insert_message(
    client: Client, *, conversation_id: str, role: str, content: str
) -> dict[str, Any]:
    """Append one message to a conversation."""
    raise NotImplementedError(f"TODO(ai_assistant): implement insert_message on '{MESSAGES_TABLE}'")
