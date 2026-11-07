"""Business logic for the Credit Learning section.

Rules implemented here (pure helpers so they are unit-testable):

- Submitting a lesson attempt (any score) marks the lesson completed and creates
  or bumps the `learning_completions` row; retakes are unlimited.
- A recap draws five random questions from lessons the user has completed.
- Any graded lesson **or recap** submission counts as activity for the day.
  Streaks are consecutive days with activity; a missed day resets the visible
  streak to 0 (computed lazily, no cron job), and the next activity starts at 1.
"""

import logging
import random
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from supabase import Client

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.sections.credit_learning import repository
from app.sections.credit_learning.schemas import (
    AnswerIn,
    AnswerResult,
    AttemptResult,
    CategoryProgress,
    CompletionRead,
    LessonAttemptRequest,
    LessonDetail,
    LessonProgress,
    LessonSummary,
    ProgressResponse,
    QuestionRead,
    RecapAttemptRequest,
    RecapResponse,
    RoadmapResponse,
    StreakRead,
)

logger = logging.getLogger(__name__)

#: Questions served by the recap button.
RECAP_QUESTION_COUNT = 5


class InvalidAttemptError(AppError):
    """Submitted answers do not match the questions being graded."""

    status_code = 422
    code = "invalid_attempt"
    message = "Submitted answers do not match the questions being graded."


# --- pure helpers -----------------------------------------------------------


def utc_today() -> date:
    """The current UTC date; streaks are counted in whole UTC days."""
    return datetime.now(UTC).date()


def as_date(value: Any) -> date | None:
    """Coerce a Supabase date/string into a `date`, preserving nulls."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        logger.warning("Unparseable streak date %r; treating it as missing", value)
        return None


def effective_streak(
    *, current_streak: int, last_activity_date: date | None, today: date
) -> int:
    """The streak to show right now: 0 once a full day has been missed."""
    if last_activity_date is None:
        return 0
    if last_activity_date >= today - timedelta(days=1):
        return current_streak
    return 0


def next_streak(
    *,
    current_streak: int,
    longest_streak: int,
    last_activity_date: date | None,
    today: date,
) -> tuple[int, int]:
    """Return `(current_streak, longest_streak)` after activity on `today`."""
    if last_activity_date is None:
        current = 1
    elif last_activity_date == today:
        current = max(current_streak, 1)
    elif last_activity_date == today - timedelta(days=1):
        current = current_streak + 1
    else:
        current = 1
    return current, max(longest_streak, current)


def grade_answers(
    questions: list[dict[str, Any]], answers: list[AnswerIn]
) -> tuple[int, list[AnswerResult]]:
    """Grade `answers` against `questions`; returns `(score, per-question results)`."""
    selected_by_question = {answer.question_id: answer.selected_index for answer in answers}
    results: list[AnswerResult] = []
    score = 0
    for question in questions:
        selected_index = selected_by_question.get(question["id"], -1)
        correct_index = int(question["correct_index"])
        correct = selected_index == correct_index
        if correct:
            score += 1
        results.append(
            AnswerResult(
                question_id=question["id"],
                selected_index=selected_index,
                correct_index=correct_index,
                correct=correct,
                explanation=question.get("explanation"),
            )
        )
    return score, results


def pick_recap_questions(
    questions: list[dict[str, Any]],
    *,
    count: int = RECAP_QUESTION_COUNT,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """Pick `count` random questions without repeats (all of them if fewer)."""
    picker = rng or random
    if len(questions) <= count:
        return picker.sample(questions, len(questions))
    return picker.sample(questions, count)


# --- shared shaping ---------------------------------------------------------


def _sorted_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """Order rows by a display-position column (stable, missing values last)."""
    return sorted(rows, key=lambda row: row.get(key) or 0)


def _question_read(
    question: dict[str, Any], lesson: dict[str, Any] | None
) -> QuestionRead:
    """Shape a question row for the API, withholding `correct_index`."""
    return QuestionRead(
        id=question["id"],
        lesson_id=question["lesson_id"],
        lesson_slug=(lesson or {}).get("slug", ""),
        lesson_title=(lesson or {}).get("title", ""),
        position=int(question["position"]),
        prompt=question["prompt"],
        options=list(question.get("options") or []),
    )


def _completed_lesson_ids(client: Client, *, user_id: str) -> list[str]:
    completions = repository.list_completions(client, user_id=user_id)
    return [completion["lesson_id"] for completion in completions]


# --- reads ------------------------------------------------------------------


def list_lessons(client: Client) -> list[LessonSummary]:
    """Return the flat lesson catalogue with question counts."""
    lessons = _sorted_rows(repository.list_lessons(client), "position")
    question_counts = Counter(
        question["lesson_id"] for question in repository.list_questions(client)
    )
    return [
        LessonSummary(
            id=lesson["id"],
            slug=lesson["slug"],
            category_id=lesson["category_id"],
            position=int(lesson["position"]),
            title=lesson["title"],
            summary=lesson["summary"],
            question_count=question_counts.get(lesson["id"], 0),
        )
        for lesson in lessons
    ]


def get_lesson(client: Client, *, slug: str) -> LessonDetail:
    """Return one lesson and its questions, raising `NotFoundError` for bad slugs."""
    lesson = repository.get_lesson_by_slug(client, slug)
    if lesson is None:
        raise NotFoundError(f"No lesson with slug '{slug}'.")
    category_title = next(
        (
            category["title"]
            for category in repository.list_categories(client)
            if category["id"] == lesson["category_id"]
        ),
        "",
    )
    questions = _sorted_rows(
        repository.list_questions(client, lesson_id=lesson["id"]), "position"
    )
    return LessonDetail(
        id=lesson["id"],
        slug=lesson["slug"],
        category_id=lesson["category_id"],
        category_title=category_title,
        position=int(lesson["position"]),
        title=lesson["title"],
        summary=lesson["summary"],
        questions=[_question_read(question, lesson) for question in questions],
    )


def get_streak(client: Client, *, user_id: str) -> StreakRead:
    """Return the user's streak with the lazy missed-day reset applied."""
    row = repository.get_streak(client, user_id=user_id)
    today = utc_today()
    if row is None:
        return StreakRead(
            current_streak=0,
            longest_streak=0,
            last_activity_date=None,
            active_today=False,
        )
    last_activity_date = as_date(row.get("last_activity_date"))
    return StreakRead(
        current_streak=effective_streak(
            current_streak=int(row.get("current_streak") or 0),
            last_activity_date=last_activity_date,
            today=today,
        ),
        longest_streak=int(row.get("longest_streak") or 0),
        last_activity_date=last_activity_date,
        active_today=last_activity_date == today,
    )


def get_roadmap(client: Client, *, user_id: str) -> RoadmapResponse:
    """Return every category and lesson annotated with the user's progress."""
    categories = _sorted_rows(repository.list_categories(client), "position")
    lessons = _sorted_rows(repository.list_lessons(client), "position")
    question_counts = Counter(
        question["lesson_id"] for question in repository.list_questions(client)
    )
    completion_by_lesson = {
        completion["lesson_id"]: completion
        for completion in repository.list_completions(client, user_id=user_id)
    }

    lessons_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lesson in lessons:
        lessons_by_category[lesson["category_id"]].append(lesson)

    category_models: list[CategoryProgress] = []
    for category in categories:
        lesson_models: list[LessonProgress] = []
        for lesson in lessons_by_category.get(category["id"], []):
            completion = completion_by_lesson.get(lesson["id"])
            lesson_models.append(
                LessonProgress(
                    id=lesson["id"],
                    slug=lesson["slug"],
                    category_id=lesson["category_id"],
                    position=int(lesson["position"]),
                    title=lesson["title"],
                    summary=lesson["summary"],
                    question_count=question_counts.get(lesson["id"], 0),
                    completed=completion is not None,
                    attempts=int(completion["attempts"]) if completion else 0,
                    best_score=int(completion["best_score"]) if completion else None,
                    last_completed_at=completion.get("last_completed_at")
                    if completion
                    else None,
                )
            )
        category_models.append(
            CategoryProgress(
                id=category["id"],
                title=category["title"],
                position=int(category["position"]),
                lessons=lesson_models,
            )
        )

    return RoadmapResponse(
        streak=get_streak(client, user_id=user_id), categories=category_models
    )


def get_progress(client: Client, *, user_id: str) -> ProgressResponse:
    """Return the completed lessons (with attempt stats) and the streak."""
    lesson_by_id = {
        lesson["id"]: lesson for lesson in repository.list_lessons(client)
    }
    completions: list[CompletionRead] = []
    for completion in repository.list_completions(client, user_id=user_id):
        lesson = lesson_by_id.get(completion["lesson_id"])
        if lesson is None:
            continue
        completions.append(
            CompletionRead(
                lesson_id=lesson["id"],
                lesson_slug=lesson["slug"],
                lesson_title=lesson["title"],
                attempts=int(completion["attempts"]),
                last_score=int(completion["last_score"]),
                best_score=int(completion["best_score"]),
                first_completed_at=completion.get("first_completed_at"),
                last_completed_at=completion.get("last_completed_at"),
            )
        )
    return ProgressResponse(
        streak=get_streak(client, user_id=user_id), completions=completions
    )


def get_recap(
    client: Client,
    *,
    user_id: str,
    count: int = RECAP_QUESTION_COUNT,
    rng: random.Random | None = None,
) -> RecapResponse:
    """Serve `count` random questions from lessons the user has completed."""
    lesson_ids = _completed_lesson_ids(client, user_id=user_id)
    if not lesson_ids:
        raise ConflictError("Complete a lesson before starting a recap.")
    questions = repository.list_questions_for_lessons(client, lesson_ids=lesson_ids)
    if not questions:
        raise ConflictError("No recap questions are available yet.")
    lesson_by_id = {
        lesson["id"]: lesson for lesson in repository.list_lessons(client)
    }
    picked = pick_recap_questions(questions, count=count, rng=rng)
    return RecapResponse(
        questions=[
            _question_read(question, lesson_by_id.get(question["lesson_id"]))
            for question in picked
        ]
    )


# --- attempts ---------------------------------------------------------------


def _validate_lesson_answers(
    questions: list[dict[str, Any]], answers: list[AnswerIn]
) -> None:
    """Require exactly this lesson's questions, each answered once."""
    answered = [answer.question_id for answer in answers]
    if len(set(answered)) != len(answered):
        raise InvalidAttemptError("Each question can only be answered once.")
    if set(answered) != {question["id"] for question in questions}:
        raise InvalidAttemptError("Answers must cover exactly this lesson's questions.")


def _validate_recap_answers(available: set[str], answers: list[AnswerIn]) -> None:
    """Require the served number of distinct answers from completed lessons."""
    answered = [answer.question_id for answer in answers]
    if len(set(answered)) != len(answered):
        raise InvalidAttemptError("Each question can only be answered once.")
    if not set(answered) <= available:
        raise InvalidAttemptError(
            "Recap answers must come from lessons you have completed."
        )
    required = min(RECAP_QUESTION_COUNT, len(available))
    if len(answered) != required:
        raise InvalidAttemptError(f"Answer exactly {required} recap questions.")


def _save_completion(
    client: Client,
    *,
    user_id: str,
    lesson_id: str,
    score: int,
    now: datetime,
) -> None:
    """Create or bump the user's completion row (retakes are unlimited)."""
    existing = repository.get_completion(client, user_id=user_id, lesson_id=lesson_id)
    if existing:
        attempts = int(existing["attempts"]) + 1
        best_score = max(int(existing["best_score"]), score)
        first_completed_at = existing.get("first_completed_at")
    else:
        attempts = 1
        best_score = score
        first_completed_at = now.isoformat()
    repository.upsert_completion(
        client,
        user_id=user_id,
        payload={
            "lesson_id": lesson_id,
            "attempts": attempts,
            "last_score": score,
            "best_score": best_score,
            "first_completed_at": first_completed_at,
            "last_completed_at": now.isoformat(),
        },
    )


def _save_attempt(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> None:
    """Record one graded submission for history/analytics."""
    repository.insert_attempt(client, user_id=user_id, payload=payload)


def _record_activity(client: Client, *, user_id: str, today: date) -> StreakRead:
    """Count today's lesson/recap submission towards the streak and return it."""
    row = repository.get_streak(client, user_id=user_id) or {}
    current_streak, longest_streak = next_streak(
        current_streak=int(row.get("current_streak") or 0),
        longest_streak=int(row.get("longest_streak") or 0),
        last_activity_date=as_date(row.get("last_activity_date")),
        today=today,
    )
    repository.upsert_streak(
        client,
        user_id=user_id,
        payload={
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": today.isoformat(),
        },
    )
    return StreakRead(
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_activity_date=today,
        active_today=True,
    )


def submit_lesson_attempt(
    client: Client, *, slug: str, request: LessonAttemptRequest
) -> AttemptResult:
    """Grade a lesson attempt, mark the lesson completed and extend the streak."""
    lesson = repository.get_lesson_by_slug(client, slug)
    if lesson is None:
        raise NotFoundError(f"No lesson with slug '{slug}'.")
    questions = _sorted_rows(
        repository.list_questions(client, lesson_id=lesson["id"]), "position"
    )
    if not questions:
        raise ConflictError("This lesson has no questions yet.")

    _validate_lesson_answers(questions, request.answers)
    score, results = grade_answers(questions, request.answers)

    now = datetime.now(UTC)
    _save_completion(
        client, user_id=request.user_id, lesson_id=lesson["id"], score=score, now=now
    )
    _save_attempt(
        client,
        user_id=request.user_id,
        payload={
            "kind": "lesson",
            "lesson_id": lesson["id"],
            "question_ids": [question["id"] for question in questions],
            "score": score,
            "total": len(questions),
        },
    )
    streak = _record_activity(client, user_id=request.user_id, today=now.date())

    return AttemptResult(
        kind="lesson",
        lesson_id=lesson["id"],
        score=score,
        total=len(questions),
        answers=results,
        streak=streak,
    )


def submit_recap_attempt(
    client: Client, *, request: RecapAttemptRequest
) -> AttemptResult:
    """Grade a recap attempt and count it towards the streak."""
    lesson_ids = _completed_lesson_ids(client, user_id=request.user_id)
    if not lesson_ids:
        raise ConflictError("Complete a lesson before starting a recap.")
    questions = repository.list_questions_for_lessons(client, lesson_ids=lesson_ids)
    if not questions:
        raise ConflictError("No recap questions are available yet.")

    available = {question["id"] for question in questions}
    _validate_recap_answers(available, request.answers)

    answered_ids = {answer.question_id for answer in request.answers}
    picked = [question for question in questions if question["id"] in answered_ids]
    score, results = grade_answers(picked, request.answers)

    now = datetime.now(UTC)
    _save_attempt(
        client,
        user_id=request.user_id,
        payload={
            "kind": "recap",
            "lesson_id": None,
            "question_ids": [question["id"] for question in picked],
            "score": score,
            "total": len(picked),
        },
    )
    streak = _record_activity(client, user_id=request.user_id, today=now.date())

    return AttemptResult(
        kind="recap",
        lesson_id=None,
        score=score,
        total=len(picked),
        answers=results,
        streak=streak,
    )
