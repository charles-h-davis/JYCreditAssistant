"""Supabase access for the Credit Learning section.

Tables (see `schema.sql` next to this file):

- ``learning_categories`` / ``learning_lessons`` / ``learning_questions`` content.
- ``learning_completions`` per-user, per-lesson progress (one row, retakes bump it).
- ``learning_attempts``     every graded submission (lessons and recaps).
- ``learning_streaks``      one row per user with the current/longest streak.

Reads of content are public; progress writes are user-scoped. The backend uses
the service-role client (no JWT auth yet) and passes an explicit ``user_id``;
``TODO(credit_learning)``: switch to ``get_supabase`` + RLS once auth exists.
"""

from typing import Any

from supabase import Client

CATEGORIES_TABLE = "learning_categories"
LESSONS_TABLE = "learning_lessons"
QUESTIONS_TABLE = "learning_questions"
COMPLETIONS_TABLE = "learning_completions"
ATTEMPTS_TABLE = "learning_attempts"
STREAKS_TABLE = "learning_streaks"


# --- content ---------------------------------------------------------------


def list_categories(client: Client) -> list[dict[str, Any]]:
    """Return every roadmap category in display order."""
    response = client.table(CATEGORIES_TABLE).select("*").order("position").execute()
    return response.data or []


def list_lessons(client: Client) -> list[dict[str, Any]]:
    """Return published lessons in display order."""
    response = (
        client.table(LESSONS_TABLE)
        .select("*")
        .eq("is_published", True)
        .order("position")
        .execute()
    )
    return response.data or []


def get_lesson_by_slug(client: Client, slug: str) -> dict[str, Any] | None:
    """Return a single published lesson row, or None when no lesson matches."""
    response = (
        client.table(LESSONS_TABLE)
        .select("*")
        .eq("slug", slug)
        .eq("is_published", True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def list_questions(
    client: Client, *, lesson_id: str | None = None
) -> list[dict[str, Any]]:
    """Return questions in order, optionally limited to one lesson."""
    query = client.table(QUESTIONS_TABLE).select("*").order("position")
    if lesson_id is not None:
        query = query.eq("lesson_id", lesson_id)
    response = query.execute()
    return response.data or []


def get_question(client: Client, *, question_id: str) -> dict[str, Any] | None:
    """Return one question row (including its correct answer), or None."""
    response = (
        client.table(QUESTIONS_TABLE)
        .select("*")
        .eq("id", question_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def list_questions_for_lessons(
    client: Client, *, lesson_ids: list[str]
) -> list[dict[str, Any]]:
    """Return every question belonging to the given lessons (used by recap)."""
    if not lesson_ids:
        return []
    response = (
        client.table(QUESTIONS_TABLE)
        .select("*")
        .in_("lesson_id", lesson_ids)
        .order("position")
        .execute()
    )
    return response.data or []


# --- progress --------------------------------------------------------------


def get_completion(
    client: Client, *, user_id: str, lesson_id: str
) -> dict[str, Any] | None:
    """Return the user's progress row for one lesson, or None."""
    response = (
        client.table(COMPLETIONS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("lesson_id", lesson_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def list_completions(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return all completed lessons for a user, most recent first."""
    response = (
        client.table(COMPLETIONS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("last_completed_at", desc=True)
        .execute()
    )
    return response.data or []


def upsert_completion(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert/update one lesson completion, keyed on `(user_id, lesson_id)`."""
    row = {"user_id": user_id, **payload}
    response = (
        client.table(COMPLETIONS_TABLE)
        .upsert(row, on_conflict="user_id,lesson_id")
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else row


def insert_attempt(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Record one graded submission (lesson or recap)."""
    row = {"user_id": user_id, **payload}
    response = client.table(ATTEMPTS_TABLE).insert(row).execute()
    rows = response.data or []
    return rows[0] if rows else row


# --- streaks ---------------------------------------------------------------


def get_streak(client: Client, *, user_id: str) -> dict[str, Any] | None:
    """Return the user's streak row, or None when they have no activity yet."""
    response = (
        client.table(STREAKS_TABLE)
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def upsert_streak(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert/update the user's streak, keyed on `user_id`."""
    row = {"user_id": user_id, **payload}
    response = client.table(STREAKS_TABLE).upsert(row, on_conflict="user_id").execute()
    rows = response.data or []
    return rows[0] if rows else row


# --- seeding ---------------------------------------------------------------


def upsert_category(client: Client, *, payload: dict[str, Any]) -> dict[str, Any]:
    """Insert/update one category row, keyed on its slug id."""
    response = (
        client.table(CATEGORIES_TABLE).upsert(payload, on_conflict="id").execute()
    )
    rows = response.data or []
    return rows[0] if rows else payload


def upsert_lesson(client: Client, *, payload: dict[str, Any]) -> dict[str, Any]:
    """Insert/update one lesson row, keyed on its slug."""
    response = (
        client.table(LESSONS_TABLE).upsert(payload, on_conflict="slug").execute()
    )
    rows = response.data or []
    return rows[0] if rows else payload


def upsert_question(client: Client, *, payload: dict[str, Any]) -> dict[str, Any]:
    """Insert/update one question, keyed on `(lesson_id, position)`."""
    response = (
        client.table(QUESTIONS_TABLE)
        .upsert(payload, on_conflict="lesson_id,position")
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else payload
