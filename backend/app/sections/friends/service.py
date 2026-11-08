"""Business logic for the Friends section.

Emails are normalised before anything is stored, the display name is derived from
the address when the caller does not supply one, and adding somebody twice is a
conflict rather than a duplicate row.
"""

import re
from typing import Any

from supabase import Client

from app.core.exceptions import ConflictError, NotFoundError
from app.sections.friends import repository
from app.sections.friends.schemas import FriendCreate, FriendRead

#: Local-part separators that become spaces in a derived display name.
_NAME_SEPARATORS = re.compile(r"[._\-]+")
#: PostgREST/Postgres unique-violation code.
_UNIQUE_VIOLATION = "23505"


def normalize_email(email: str) -> str:
    """Trim and lower-case an address so 'A@B.com ' and 'a@b.com' are one friend."""
    return email.strip().lower()


def display_name_from_email(email: str) -> str:
    """Derive a friendly name: 'james.may+credit@example.com' -> 'James May'."""
    local = normalize_email(email).split("@", 1)[0].split("+", 1)[0]
    tokens = [token for token in _NAME_SEPARATORS.split(local) if token]
    if not tokens:
        return normalize_email(email)
    return " ".join(token[:1].upper() + token[1:].lower() for token in tokens)


def _is_duplicate(exc: Exception) -> bool:
    """True when Postgres rejected a row because the friend already exists."""
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code == _UNIQUE_VIOLATION
    args = getattr(exc, "args", ())
    if args and isinstance(args[0], dict):
        return args[0].get("code") == _UNIQUE_VIOLATION
    return False


def _friend_read(row: dict[str, Any]) -> FriendRead:
    """Build a `FriendRead` from a stored row (tolerating a sparse insert result)."""
    return FriendRead(
        id=str(row.get("id", "")),
        user_id=str(row.get("user_id", "")),
        friend_name=str(row.get("friend_name", "")),
        friend_email=str(row.get("friend_email", "")),
        created_at=row.get("created_at"),
    )


def list_friends(client: Client, *, user_id: str) -> list[FriendRead]:
    """Return the user's friends, most recently added first."""
    return [_friend_read(row) for row in repository.list_friends(client, user_id=user_id)]


def add_friend(client: Client, *, request: FriendCreate) -> FriendRead:
    """Add a friend by email; a second attempt for the same address is a 409."""
    email = normalize_email(request.email)
    if repository.get_friend(client, user_id=request.user_id, email=email) is not None:
        raise ConflictError(f"{email} is already in your friends.")

    name = (request.name or "").strip() or display_name_from_email(email)
    try:
        row = repository.insert_friend(
            client,
            user_id=request.user_id,
            payload={"friend_name": name, "friend_email": email},
        )
    except Exception as exc:  # noqa: BLE001 - mapped below, re-raised otherwise
        if _is_duplicate(exc):
            raise ConflictError(f"{email} is already in your friends.") from exc
        raise
    return _friend_read(row)


def remove_friend(client: Client, *, user_id: str, friend_id: str) -> None:
    """Remove one friend from the user's list, or raise 404."""
    removed = repository.delete_friend(client, user_id=user_id, friend_id=friend_id)
    if not removed:
        raise NotFoundError("That friend is not in your list.")
