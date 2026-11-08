"""Give the user's friends something to have done.

Writes one row per event into ``friends_feed_entries`` with ``actor`` set to the
friend's name, so the feed is a plain table read instead of hardcoded data. Events
borrow real lesson titles from the Credit Learning content, so a friend
"completes" a lesson that actually exists in the app.

Re-running replaces the friend activity for that user and leaves the user's own
completions alone.

Usage (from backend/):

    ../.venv/Scripts/python.exe -m app.sections.friends_feed.seed            # demo
    ../.venv/Scripts/python.exe -m app.sections.friends_feed.seed <user-id>
"""

import logging
import random
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.credit_learning.content import CATEGORIES
from app.sections.friends import repository as friends_repository
from app.sections.friends import seed as friends_seed
from app.sections.friends_feed import repository
from app.sections.friends_feed.service import SELF_ACTOR

logger = logging.getLogger(__name__)

#: Streak lengths a friend might have reached.
STREAK_DAYS = (3, 5, 7, 10, 14, 21, 30)
#: Generated activity is spread over the last three days, ending a few minutes ago.
SPREAD_MINUTES = 3 * 24 * 60
FIRST_MINUTE = 12
#: A couple of friends get a second event, so the feed is not one row per person.
EXTRA_EVENTS = 3
#: Kinds to draw from; lessons dominate, as they do in real use.
KIND_POOL = ("lesson", "lesson", "lesson", "streak", "recap")


def lesson_titles() -> list[tuple[str, int]]:
    """Every lesson as ``("Category — Lesson", question_count)``."""
    return [
        (f"{category.title} — {lesson.title}", len(lesson.questions))
        for category in CATEGORIES
        for lesson in category.lessons
    ]


def _event(rng: random.Random, lessons: list[tuple[str, int]], kind: str) -> dict[str, Any]:
    """Build one friend event of the given kind, with the API's wording."""
    if kind == "streak":
        days = rng.choice(STREAK_DAYS)
        return {"kind": "streak", "action": f"achieved a {days} day streak", "detail": None}

    if kind == "recap":
        score = rng.randint(3, 5)
        return {
            "kind": "recap",
            "action": "finished a refresh round",
            "detail": f"{score}/5 correct",
        }

    title, total = rng.choice(lessons)
    score = rng.randint(max(1, total - 2), total)
    return {"kind": "lesson", "action": f"completed {title}", "detail": f"{score}/{total} correct"}


def build_activity(
    actors: list[str],
    *,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """Build the friend rows to insert: one event per friend, plus a few extras."""
    if not actors:
        return []

    reference = now or datetime.now(UTC)
    random_source = rng or random.Random(0)
    lessons = lesson_titles()

    slots: list[tuple[str, str]] = [(actor, "lesson") for actor in actors]
    for actor in random_source.sample(actors, k=min(EXTRA_EVENTS, len(actors))):
        slots.append((actor, random_source.choice(KIND_POOL)))

    offsets = random_source.sample(
        range(FIRST_MINUTE, SPREAD_MINUTES), k=len(slots)
    )
    rows: list[dict[str, Any]] = []
    for (actor, kind), minutes_ago in zip(slots, offsets, strict=True):
        event = _event(random_source, lessons, kind)
        rows.append(
            {
                "actor": actor,
                **event,
                "created_at": (reference - timedelta(minutes=minutes_ago)).isoformat(),
            }
        )
    return rows


def run(client: Client, user_id: str) -> int:
    """Replace the friend activity for one user; return how many rows were written."""
    friends = friends_repository.list_friends(client, user_id=user_id)
    actors = [
        str(friend.get("friend_name") or friend.get("friend_email") or "A friend")
        for friend in friends
    ]
    if not actors:
        logger.warning("%s has no friends yet — add one, then re-run the seed.", user_id)
        return 0

    removed = repository.delete_entries_from_others(
        client, user_id=user_id, self_actor=SELF_ACTOR
    )
    rows = build_activity(actors, rng=random.Random(user_id))
    written = repository.insert_entries(client, user_id=user_id, payloads=rows)
    logger.info(
        "Friend activity for %s: replaced %d row(s) with %d", user_id, removed, written
    )
    return written


def main() -> None:
    """Generate friend activity for the demo account (or a given user id)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    client = get_supabase_admin()
    user_id = sys.argv[1] if len(sys.argv) > 1 else friends_seed.resolve_user_id(client)
    count = run(client, user_id)
    logger.info("Generated %d friend event(s) for %s", count, user_id)


if __name__ == "__main__":
    main()
