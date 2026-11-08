"""Load the demo friends into the demo account.

Idempotent: rows are upserted on `(user_id, friend_email)`, so re-running never
duplicates a friend. `backend/scripts/seed_demo.py` calls `run` as part of the
full demo seed.

Usage (from backend/):

    ../.venv/Scripts/python.exe -m app.sections.friends.seed            # demo account
    ../.venv/Scripts/python.exe -m app.sections.friends.seed <user-id>  # anyone

Without an id the demo account (`demo@demo.com`) is resolved through the Supabase
admin API.
"""

import logging
import sys

from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.friends import repository
from app.sections.friends.content import DEFAULT_FRIENDS
from app.sections.friends.service import normalize_email

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@demo.com"
#: The admin API paginates at 50 users per page; five pages is plenty for a demo.
_MAX_PAGES = 5


def run(client: Client, user_id: str) -> int:
    """Upsert every demo friend for one user and return how many were written."""
    for friend in DEFAULT_FRIENDS:
        repository.upsert_friend(
            client,
            user_id=user_id,
            payload={
                "friend_name": friend.name,
                "friend_email": normalize_email(friend.email),
            },
        )
    return len(DEFAULT_FRIENDS)


def resolve_user_id(client: Client, email: str = DEMO_EMAIL) -> str:
    """Find an auth user id by email (the demo account, by default)."""
    wanted = email.strip().lower()
    for page in range(1, _MAX_PAGES + 1):
        users = client.auth.admin.list_users(page=page, per_page=50)
        if not users:
            break
        for user in users:
            if (user.email or "").strip().lower() == wanted:
                return str(user.id)
    raise RuntimeError(
        f"No {email} user found — run backend/scripts/seed_demo.py first, "
        "or pass a user id explicitly."
    )


def main() -> None:
    """Seed the demo friends against the configured Supabase project."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    client = get_supabase_admin()
    user_id = sys.argv[1] if len(sys.argv) > 1 else resolve_user_id(client)
    count = run(client, user_id)
    logger.info("Loaded %d demo friend(s) for user %s", count, user_id)


if __name__ == "__main__":
    main()
