"""Business logic for the Friends Feed section.

The feed is a plain read of ``friends_feed_entries``: one row per event, written
either by the app (the user finishing a lesson) or by ``seed.py`` (their friends'
activity). Rows come back newest first, so the endpoint simply cuts them to size —
nothing is invented at request time.
"""

from datetime import UTC, datetime
from typing import Any

from supabase import Client

from app.sections.friends_feed import repository
from app.sections.friends_feed.schemas import (
    FeedEntry,
    FeedEntryCreate,
    FeedKind,
    FriendsFeedResponse,
)

#: Entries returned when the caller does not ask for a size.
DEFAULT_LIMIT = 12
#: Hard ceiling, so one request can never ask for the whole table.
MAX_LIMIT = 40
#: How the caller's own activity is labelled — and how friend rows are told apart.
SELF_ACTOR = "You"


def _as_datetime(value: Any) -> datetime:
    """Parse a PostgREST timestamp ('Z' or offset) into an aware UTC datetime."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(UTC)
    else:
        return datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def stored_entries(rows: list[dict[str, Any]]) -> list[FeedEntry]:
    """Stored rows as feed entries; ``actor`` decides whether it is the user's own."""
    return [
        FeedEntry(
            id=str(row.get("id", "")),
            actor=str(row.get("actor") or SELF_ACTOR),
            kind=row.get("kind") or "lesson",
            action=str(row.get("action", "")),
            detail=row.get("detail"),
            occurred_at=_as_datetime(row.get("created_at")),
            is_self=str(row.get("actor") or SELF_ACTOR) == SELF_ACTOR,
        )
        for row in rows
    ]


def get_feed(
    client: Client, *, user_id: str, limit: int = DEFAULT_LIMIT
) -> FriendsFeedResponse:
    """Return the latest entries for this user — their own activity and their friends'."""
    size = max(1, min(limit, MAX_LIMIT))
    rows = repository.list_entries(client, user_id=user_id, limit=size)
    return FriendsFeedResponse(entries=stored_entries(rows))


def _compose(request: FeedEntryCreate) -> tuple[FeedKind, str, str]:
    """Return the stored ``(kind, action, detail)`` for one submission."""
    detail = f"{request.score}/{request.total} correct"
    if request.kind == "recap":
        return "recap", "finished a refresh round", detail
    return "lesson", f"completed {(request.lesson_title or '').strip()}", detail


def record_entry(client: Client, *, request: FeedEntryCreate) -> FeedEntry:
    """Persist one finished lesson / refresh round and return it as a feed entry."""
    kind, action, detail = _compose(request)
    row = repository.insert_entry(
        client,
        user_id=request.user_id,
        payload={"kind": kind, "actor": SELF_ACTOR, "action": action, "detail": detail},
    )
    return stored_entries([row])[0]

