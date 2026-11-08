"""Tests for the Credit Learning section.

Credential-free: the Supabase dependency is overridden and the repository module
is replaced with an in-memory fake seeded from the real roadmap content.
"""

import random
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_supabase_admin
from app.main import app
from app.sections.credit_learning import repository, seed, service
from app.sections.credit_learning.content import CATEGORIES
from app.sections.credit_learning.schemas import AnswerIn

SECTION = "credit-learning"
USER_ID = "11111111-1111-1111-1111-111111111111"


def _lesson_id(slug: str) -> str:
    return f"lesson-{slug}"


def _question_id(slug: str, position: int) -> str:
    return f"question-{slug}-{position}"


def _correct_answers(slug: str) -> list[dict[str, Any]]:
    """All-correct answer payload for one lesson, shaped like the API request."""
    lesson = next(
        lesson
        for category in CATEGORIES
        for lesson in category.lessons
        if lesson.slug == slug
    )
    return [
        {
            "question_id": _question_id(lesson.slug, question.position),
            "selected_index": question.correct_index,
        }
        for question in lesson.questions
    ]


class FakeRepository:
    """In-memory stand-in for `repository`, seeded from the real content."""

    def __init__(self) -> None:
        self.categories = [
            {"id": category.id, "title": category.title, "position": category.position}
            for category in CATEGORIES
        ]
        self.lessons = [
            {
                "id": _lesson_id(lesson.slug),
                "slug": lesson.slug,
                "category_id": category.id,
                "position": lesson.position,
                "title": lesson.title,
                "summary": lesson.summary,
                "is_published": True,
            }
            for category in CATEGORIES
            for lesson in category.lessons
        ]
        self.questions = [
            {
                "id": _question_id(lesson.slug, question.position),
                "lesson_id": _lesson_id(lesson.slug),
                "position": question.position,
                "prompt": question.prompt,
                "options": list(question.options),
                "correct_index": question.correct_index,
                "explanation": question.explanation,
            }
            for category in CATEGORIES
            for lesson in category.lessons
            for question in lesson.questions
        ]
        self.completions: dict[tuple[str, str], dict[str, Any]] = {}
        self.attempts: list[dict[str, Any]] = []
        self.streaks: dict[str, dict[str, Any]] = {}
        self.seeded = {"categories": 0, "lessons": 0, "questions": 0}

    # content
    def list_categories(self, client: Any) -> list[dict[str, Any]]:
        return list(self.categories)

    def list_lessons(self, client: Any) -> list[dict[str, Any]]:
        return list(self.lessons)

    def get_lesson_by_slug(self, client: Any, slug: str) -> dict[str, Any] | None:
        return next((lesson for lesson in self.lessons if lesson["slug"] == slug), None)

    def list_questions(
        self, client: Any, *, lesson_id: str | None = None
    ) -> list[dict[str, Any]]:
        if lesson_id is None:
            return list(self.questions)
        return [question for question in self.questions if question["lesson_id"] == lesson_id]

    def list_questions_for_lessons(
        self, client: Any, *, lesson_ids: list[str]
    ) -> list[dict[str, Any]]:
        wanted = set(lesson_ids)
        return [question for question in self.questions if question["lesson_id"] in wanted]

    def get_question(self, client: Any, *, question_id: str) -> dict[str, Any] | None:
        return next(
            (question for question in self.questions if question["id"] == question_id),
            None,
        )

    # progress
    def get_completion(
        self, client: Any, *, user_id: str, lesson_id: str
    ) -> dict[str, Any] | None:
        return self.completions.get((user_id, lesson_id))

    def list_completions(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        return [row for (owner, _), row in self.completions.items() if owner == user_id]

    def upsert_completion(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        key = (user_id, payload["lesson_id"])
        row = {**self.completions.get(key, {}), "user_id": user_id, **payload}
        self.completions[key] = row
        return row

    def insert_attempt(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        row = {"id": f"attempt-{len(self.attempts) + 1}", "user_id": user_id, **payload}
        self.attempts.append(row)
        return row

    # streaks
    def get_streak(self, client: Any, *, user_id: str) -> dict[str, Any] | None:
        return self.streaks.get(user_id)

    def upsert_streak(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        row = {**self.streaks.get(user_id, {}), "user_id": user_id, **payload}
        self.streaks[user_id] = row
        return row

    # seeding
    def upsert_category(self, client: Any, *, payload: dict[str, Any]) -> dict[str, Any]:
        self.seeded["categories"] += 1
        return payload

    def upsert_lesson(self, client: Any, *, payload: dict[str, Any]) -> dict[str, Any]:
        self.seeded["lessons"] += 1
        return {**payload, "id": _lesson_id(payload["slug"])}

    def upsert_question(self, client: Any, *, payload: dict[str, Any]) -> dict[str, Any]:
        self.seeded["questions"] += 1
        return payload


REPOSITORY_FUNCTIONS = (
    "list_categories",
    "list_lessons",
    "get_lesson_by_slug",
    "list_questions",
    "list_questions_for_lessons",
    "get_question",
    "get_completion",
    "list_completions",
    "upsert_completion",
    "insert_attempt",
    "get_streak",
    "upsert_streak",
    "upsert_category",
    "upsert_lesson",
    "upsert_question",
)


@pytest.fixture(autouse=True)
def offline_dependencies() -> Iterator[None]:
    """Keep the endpoint tests offline with a fake database client."""
    app.dependency_overrides[get_supabase_admin] = lambda: object()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> FakeRepository:
    """Replace every repository call with an in-memory store."""
    fake = FakeRepository()
    for name in REPOSITORY_FUNCTIONS:
        monkeypatch.setattr(repository, name, getattr(fake, name))
    return fake


# --- content ---------------------------------------------------------------


def test_content_shape() -> None:
    expected_categories = [
        "credit-basics",
        "financial-arithmetic",
        "budgeting-and-affordability",
        "comparing-credit-options",
        "managing-repayments",
    ]

    assert [category.id for category in CATEGORIES] == expected_categories
    assert [category.position for category in CATEGORIES] == [1, 2, 3, 4, 5]

    slugs: set[str] = set()
    for category in CATEGORIES:
        assert len(category.lessons) == 3
        assert [lesson.position for lesson in category.lessons] == [1, 2, 3]
        for lesson in category.lessons:
            assert lesson.slug not in slugs
            slugs.add(lesson.slug)
            assert lesson.title and lesson.summary
            assert len(lesson.questions) == 5
            assert [question.position for question in lesson.questions] == [1, 2, 3, 4, 5]
            for question in lesson.questions:
                assert question.prompt and question.explanation
                assert len(question.options) == 4
                assert len(set(question.options)) == 4
                assert 0 <= question.correct_index <= 3


def test_seed_writes_the_whole_roadmap(store: FakeRepository) -> None:
    counts = seed.run(object())

    assert counts == {"categories": 5, "lessons": 15, "questions": 75}
    assert store.seeded == counts


# --- streak ----------------------------------------------------------------


TODAY = date(2026, 7, 11)


def test_effective_streak_keeps_yesterday() -> None:
    assert (
        service.effective_streak(
            current_streak=3,
            last_activity_date=TODAY - timedelta(days=1),
            today=TODAY,
        )
        == 3
    )


def test_effective_streak_resets_after_a_missed_day() -> None:
    assert (
        service.effective_streak(
            current_streak=3,
            last_activity_date=TODAY - timedelta(days=2),
            today=TODAY,
        )
        == 0
    )


def test_effective_streak_without_activity() -> None:
    assert (
        service.effective_streak(
            current_streak=0, last_activity_date=None, today=TODAY
        )
        == 0
    )


def test_next_streak_same_day_is_unchanged() -> None:
    assert service.next_streak(
        current_streak=3,
        longest_streak=5,
        last_activity_date=TODAY,
        today=TODAY,
    ) == (3, 5)


def test_next_streak_consecutive_day_increments() -> None:
    assert service.next_streak(
        current_streak=3,
        longest_streak=3,
        last_activity_date=TODAY - timedelta(days=1),
        today=TODAY,
    ) == (4, 4)


def test_next_streak_after_a_gap_restarts() -> None:
    assert service.next_streak(
        current_streak=3,
        longest_streak=7,
        last_activity_date=TODAY - timedelta(days=3),
        today=TODAY,
    ) == (1, 7)


def test_next_streak_first_activity() -> None:
    assert service.next_streak(
        current_streak=0,
        longest_streak=0,
        last_activity_date=None,
        today=TODAY,
    ) == (1, 1)


# --- grading + recap selection ---------------------------------------------


def test_grade_answers_scores_correct_and_reports_details() -> None:
    questions = [
        {"id": "q1", "correct_index": 2, "explanation": "Because."},
        {"id": "q2", "correct_index": 0, "explanation": None},
    ]
    answers = [
        AnswerIn(question_id="q1", selected_index=2),
        AnswerIn(question_id="q2", selected_index=3),
    ]

    score, results = service.grade_answers(questions, answers)

    assert score == 1
    assert results[0].correct is True
    assert results[0].correct_index == 2
    assert results[0].explanation == "Because."
    assert results[1].correct is False
    assert results[1].selected_index == 3


def test_pick_recap_questions_returns_five_unique() -> None:
    questions = [{"id": f"q{index}"} for index in range(10)]

    picked = service.pick_recap_questions(questions, rng=random.Random(0))

    assert len(picked) == 5
    assert len({question["id"] for question in picked}) == 5


def test_pick_recap_questions_returns_all_when_fewer() -> None:
    questions = [{"id": "q1"}, {"id": "q2"}]

    picked = service.pick_recap_questions(questions, rng=random.Random(0))

    assert {question["id"] for question in picked} == {"q1", "q2"}


# --- endpoints -------------------------------------------------------------


def _attempt_url(api_prefix: str, slug: str) -> str:
    return f"{api_prefix}/{SECTION}/lessons/{slug}/attempt"


def _complete_lesson(api_prefix: str, client: TestClient, slug: str) -> None:
    response = client.post(
        _attempt_url(api_prefix, slug),
        json={"user_id": USER_ID, "answers": _correct_answers(slug)},
    )
    assert response.status_code == 200


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_roadmap_lists_five_categories_with_three_lessons(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/roadmap?user_id={USER_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["streak"]["current_streak"] == 0
    assert [category["id"] for category in body["categories"]] == [
        "credit-basics",
        "financial-arithmetic",
        "budgeting-and-affordability",
        "comparing-credit-options",
        "managing-repayments",
    ]
    assert all(len(category["lessons"]) == 3 for category in body["categories"])
    first_lesson = body["categories"][0]["lessons"][0]
    assert first_lesson["slug"] == "what-credit-is"
    assert first_lesson["completed"] is False
    assert first_lesson["question_count"] == 5


def test_lesson_detail_withholds_correct_answers(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/lessons/what-credit-is")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "What credit is and how it works"
    assert len(body["questions"]) == 5
    assert "correct_index" not in body["questions"][0]
    assert "explanation" not in body["questions"][0]
    assert len(body["questions"][0]["options"]) == 4


def test_unknown_lesson_returns_404(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/lessons/not-a-lesson")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_lesson_attempt_completes_lesson_and_starts_streak(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.post(
        _attempt_url(api_prefix, "what-credit-is"),
        json={"user_id": USER_ID, "answers": _correct_answers("what-credit-is")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "lesson"
    assert body["score"] == 5
    assert body["total"] == 5
    assert body["streak"]["current_streak"] == 1
    assert body["streak"]["active_today"] is True

    completion = store.completions[(USER_ID, _lesson_id("what-credit-is"))]
    assert completion["attempts"] == 1
    assert completion["best_score"] == 5
    assert store.attempts[-1]["kind"] == "lesson"


def test_retake_same_day_bumps_attempts_without_extending_streak(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _complete_lesson(api_prefix, client, "what-credit-is")

    response = client.post(
        _attempt_url(api_prefix, "what-credit-is"),
        json={"user_id": USER_ID, "answers": _correct_answers("what-credit-is")},
    )

    assert response.status_code == 200
    assert response.json()["streak"]["current_streak"] == 1
    completion = store.completions[(USER_ID, _lesson_id("what-credit-is"))]
    assert completion["attempts"] == 2


def test_lesson_attempt_requires_every_question(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    answers = _correct_answers("what-credit-is")[:-1]

    response = client.post(
        _attempt_url(api_prefix, "what-credit-is"),
        json={"user_id": USER_ID, "answers": answers},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_attempt"


def test_recap_requires_a_completed_lesson(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/recap?user_id={USER_ID}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_recap_returns_questions_from_completed_lessons(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _complete_lesson(api_prefix, client, "what-credit-is")

    response = client.get(f"{api_prefix}/{SECTION}/recap?user_id={USER_ID}")

    assert response.status_code == 200
    questions = response.json()["questions"]
    assert len(questions) == 5
    assert {question["lesson_id"] for question in questions} == {
        _lesson_id("what-credit-is")
    }
    assert "correct_index" not in questions[0]


def test_recap_attempt_counts_towards_streak(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _complete_lesson(api_prefix, client, "what-credit-is")
    recap_questions = client.get(
        f"{api_prefix}/{SECTION}/recap?user_id={USER_ID}"
    ).json()["questions"]
    answers = [
        {"question_id": question["id"], "selected_index": 0}
        for question in recap_questions
    ]

    response = client.post(
        f"{api_prefix}/{SECTION}/recap/attempt",
        json={"user_id": USER_ID, "answers": answers},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "recap"
    assert body["lesson_id"] is None
    assert body["total"] == 5
    assert body["streak"]["current_streak"] == 1
    assert store.attempts[-1]["kind"] == "recap"


def test_progress_lists_completed_lessons(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _complete_lesson(api_prefix, client, "what-credit-is")

    response = client.get(f"{api_prefix}/{SECTION}/progress?user_id={USER_ID}")

    assert response.status_code == 200
    body = response.json()
    assert len(body["completions"]) == 1
    assert body["completions"][0]["lesson_slug"] == "what-credit-is"
    assert body["completions"][0]["best_score"] == 5
    assert body["streak"]["current_streak"] == 1


# --- instant answer feedback -------------------------------------------------


def test_check_answer_confirms_the_correct_option(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    answer = _correct_answers("what-credit-is")[0]

    response = client.post(
        f"{api_prefix}/{SECTION}/questions/{answer['question_id']}/answer",
        json={"selected_index": answer["selected_index"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["correct_index"] == answer["selected_index"]
    assert body["explanation"]


def test_check_answer_flags_a_wrong_option(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    answer = _correct_answers("what-credit-is")[0]
    wrong = (answer["selected_index"] + 1) % 4

    response = client.post(
        f"{api_prefix}/{SECTION}/questions/{answer['question_id']}/answer",
        json={"selected_index": wrong},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is False
    assert body["selected_index"] == wrong
    assert body["correct_index"] == answer["selected_index"]


def test_check_answer_404_for_unknown_question(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.post(
        f"{api_prefix}/{SECTION}/questions/does-not-exist/answer",
        json={"selected_index": 0},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_check_answer_rejects_out_of_range_option(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    answer = _correct_answers("what-credit-is")[0]

    response = client.post(
        f"{api_prefix}/{SECTION}/questions/{answer['question_id']}/answer",
        json={"selected_index": 9},
    )

    assert response.status_code == 422

