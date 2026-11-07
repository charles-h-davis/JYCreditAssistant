"""Seed the credit-learning roadmap content into Supabase.

Idempotent: reruns upsert categories (by id), lessons (by slug) and questions
(by lesson_id + position), so text edits are picked up without duplicates.

Run from `backend/` after `schema.sql`:

    ..\\.venv\\Scripts\\python.exe -m app.sections.credit_learning.seed
"""

import logging

from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.credit_learning import repository
from app.sections.credit_learning.content import CATEGORIES

logger = logging.getLogger(__name__)


def run(client: Client) -> dict[str, int]:
    """Write every category, lesson and question; return the counts written."""
    counts = {"categories": 0, "lessons": 0, "questions": 0}

    for category in CATEGORIES:
        repository.upsert_category(
            client,
            payload={
                "id": category.id,
                "title": category.title,
                "position": category.position,
            },
        )
        counts["categories"] += 1

        for lesson in category.lessons:
            lesson_row = repository.upsert_lesson(
                client,
                payload={
                    "slug": lesson.slug,
                    "category_id": category.id,
                    "position": lesson.position,
                    "title": lesson.title,
                    "summary": lesson.summary,
                    "is_published": True,
                },
            )
            lesson_id = lesson_row.get("id")
            if not lesson_id:
                raise RuntimeError(
                    f"Supabase did not return an id for lesson '{lesson.slug}'."
                )
            counts["lessons"] += 1

            for question in lesson.questions:
                repository.upsert_question(
                    client,
                    payload={
                        "lesson_id": lesson_id,
                        "position": question.position,
                        "prompt": question.prompt,
                        "options": list(question.options),
                        "correct_index": question.correct_index,
                        "explanation": question.explanation,
                    },
                )
                counts["questions"] += 1

    return counts


def main() -> None:
    """Seed the content into the configured Supabase project."""
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    counts = run(get_supabase_admin())
    logger.info(
        "Seeded %(categories)d categories, %(lessons)d lessons, %(questions)d questions",
        counts,
    )


if __name__ == "__main__":
    main()
