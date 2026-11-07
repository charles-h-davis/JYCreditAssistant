"""Business logic for the Credit Learning section.

TODO(credit_learning owner):
  - `list_lessons(client)` -> published lessons mapped to `LessonSummary`.
  - `get_lesson(client, slug)` -> `LessonDetail`, raising
    `app.core.exceptions.NotFoundError` when the slug is unknown.
  - Keep content ordering/caching rules here, not in the router.
"""

from supabase import Client

from app.sections.credit_learning.schemas import LessonDetail, LessonSummary


def list_lessons(client: Client) -> list[LessonSummary]:
    """Return the published lesson catalogue."""
    raise NotImplementedError("TODO(credit_learning): implement list_lessons")


def get_lesson(client: Client, slug: str) -> LessonDetail:
    """Return one lesson by slug, raising `NotFoundError` when it does not exist."""
    raise NotImplementedError("TODO(credit_learning): implement get_lesson")
