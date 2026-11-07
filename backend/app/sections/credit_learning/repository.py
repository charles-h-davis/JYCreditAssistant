"""Supabase access for the Credit Learning section.

Table: `lessons` (TODO: create the migration in Supabase).

Lessons are public content, so reads can use the anon client; RLS should expose
only rows where `is_published = true`.
"""

from typing import Any

from supabase import Client

TABLE = "lessons"


def list_lessons(client: Client) -> list[dict[str, Any]]:
    """Return published lessons ordered for the catalogue."""
    raise NotImplementedError(f"TODO(credit_learning): implement list_lessons on '{TABLE}'")


def get_lesson_by_slug(client: Client, slug: str) -> dict[str, Any] | None:
    """Return a single published lesson row, or `None` when no lesson matches."""
    raise NotImplementedError(f"TODO(credit_learning): implement get_lesson_by_slug on '{TABLE}'")
