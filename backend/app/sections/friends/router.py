"""HTTP routes for the Friends section (mounted at /api/v1/friends).

There is no JWT auth dependency yet, so user-scoped endpoints take an explicit
``user_id`` and the router injects the service-role Supabase client; every
repository query filters on that id.

``TODO(friends)``: replace the `user_id` parameters with the Supabase JWT subject
and `get_supabase_admin` with `get_supabase` once auth exists.
"""

from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.friends import service
from app.sections.friends.schemas import FriendCreate, FriendRead

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.get("/ping", summary="Health check for the Friends section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "friends", "status": "ok"}


@router.get(
    "",
    response_model=list[FriendRead],
    summary="List the user's friends",
    responses={422: {"description": "Missing or empty user_id."}},
)
def list_friends(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the friend list (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> list[FriendRead]:
    """Return every friend on the user's list, most recently added first."""
    return service.list_friends(client, user_id=user_id)


@router.post(
    "",
    response_model=FriendRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a friend by email",
    responses={
        409: {"description": "That email is already in the user's friends."},
        422: {"description": "Missing user_id or an address that is not an email."},
    },
)
def add_friend(
    payload: FriendCreate,
    client: Client = Depends(get_supabase_admin),
) -> FriendRead:
    """Add a friend by email, deriving a display name from the address if none is given.

    Friends are contact rows the user owns — the address does not have to belong
    to a CreditMate account.
    """
    return service.add_friend(client, request=payload)


@router.delete(
    "/{friend_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a friend",
    responses={
        404: {"description": "No friend with that id on the user's list."},
        422: {"description": "Missing or empty user_id."},
    },
)
def remove_friend(
    friend_id: str,
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the friend list (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> None:
    """Delete one friend from the user's list."""
    service.remove_friend(client, user_id=user_id, friend_id=friend_id)
