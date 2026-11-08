"""HTTP routes for the Friends Feed section (mounted at /api/v1/friends-feed).

There is no JWT auth dependency yet, so user-scoped endpoints take an explicit
``user_id`` and the router injects the service-role Supabase client; every
repository query filters on that id.

``TODO(friends_feed)``: replace the `user_id` parameters with the Supabase JWT
subject and `get_supabase_admin` with `get_supabase` once auth exists.
"""

from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.friends_feed import service
from app.sections.friends_feed.schemas import (
    FeedEntry,
    FeedEntryCreate,
    FriendsFeedResponse,
)

router = APIRouter(prefix="/friends-feed", tags=["Friends Feed"])


@router.get("/ping", summary="Health check for the Friends Feed section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "friends-feed", "status": "ok"}


@router.get(
    "/feed",
    response_model=FriendsFeedResponse,
    summary="Friends' activity plus the user's own completions, newest first",
    responses={422: {"description": "Missing or empty user_id, or a limit outside 1-40."}},
)
def get_feed(
    user_id: str = Query(
        ...,
        min_length=1,
        description=(
            "Supabase auth user id whose own entries are included "
            "(temporary until JWT auth)."
        ),
    ),
    limit: int = Query(
        service.DEFAULT_LIMIT,
        ge=1,
        le=service.MAX_LIMIT,
        description="How many entries to return, newest first.",
    ),
    client: Client = Depends(get_supabase_admin),
) -> FriendsFeedResponse:
    """Return the latest feed entries: hardcoded friend activity merged with the user's own."""
    return service.get_feed(client, user_id=user_id, limit=limit)


@router.post(
    "/entries",
    response_model=FeedEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Record a finished lesson or refresh round in the feed",
    responses={
        422: {
            "description": "Missing user_id, bad score/total, or a lesson with no title."
        }
    },
)
def create_entry(
    payload: FeedEntryCreate,
    client: Client = Depends(get_supabase_admin),
) -> FeedEntry:
    """Store one finished lesson or refresh round so it appears at the top of the feed.

    The API composes the wording ("completed <lesson>", "finished a refresh
    round") so the feed copy never comes from the browser.
    """
    return service.record_entry(client, request=payload)
