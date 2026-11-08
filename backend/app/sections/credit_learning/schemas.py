"""Request/response models for the Credit Learning section.

Correct answers never leave the server in lesson or recap payloads: they come
back only after an attempt has been graded.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AttemptKind = Literal["lesson", "recap"]


class QuestionRead(BaseModel):
    """A question as shown to the learner (no correct answer)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Question row id (UUID).")
    lesson_id: str = Field(..., description="Owning lesson id.")
    lesson_slug: str = Field(..., description="Owning lesson slug.")
    lesson_title: str = Field(..., description="Owning lesson title.")
    position: int = Field(..., ge=1, description="1-based position inside the lesson.")
    prompt: str = Field(..., description="The question text.")
    options: list[str] = Field(..., description="Four answer options (index 0-3).")


class LessonSummary(BaseModel):
    """Flat catalogue entry for the lesson list screen."""

    id: str
    slug: str
    category_id: str
    position: int
    title: str
    summary: str
    question_count: int


class LessonProgress(LessonSummary):
    """Lesson plus this user's progress through it."""

    completed: bool = Field(..., description="True once the user has submitted an attempt.")
    attempts: int = Field(..., ge=0, description="Number of submissions (retakes allowed).")
    best_score: int | None = Field(default=None, description="Best score so far (out of 5).")
    last_completed_at: datetime | None = Field(default=None, description="Last attempt (UTC).")


class CategoryProgress(BaseModel):
    """One roadmap category with its lessons."""

    id: str
    title: str
    position: int
    lessons: list[LessonProgress]


class StreakRead(BaseModel):
    """The user's lesson streak."""

    current_streak: int = Field(
        ..., ge=0, description="Consecutive days with a lesson or recap; 0 once a day is missed."
    )
    longest_streak: int = Field(..., ge=0, description="Best streak ever recorded.")
    last_activity_date: date | None = Field(
        default=None, description="Last day a lesson or recap was completed (UTC)."
    )
    active_today: bool = Field(..., description="True if the user has completed something today.")


class RoadmapResponse(BaseModel):
    """The full roadmap with per-lesson progress and the streak."""

    streak: StreakRead
    categories: list[CategoryProgress]


class LessonDetail(BaseModel):
    """A lesson with its summary and five questions (answers withheld)."""

    id: str
    slug: str
    category_id: str
    category_title: str
    position: int
    title: str
    summary: str
    questions: list[QuestionRead]


class AnswerIn(BaseModel):
    """One answer submitted by the learner."""

    question_id: str = Field(..., min_length=1, description="Question being answered.")
    selected_index: int = Field(..., ge=0, le=3, description="Chosen option index (0-3).")


class LessonAttemptRequest(BaseModel):
    """Submit answers for one lesson (any score counts as completed)."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id (UUID) that owns progress. Temporary until JWT auth.",
    )
    answers: list[AnswerIn] = Field(
        ..., min_length=1, description="Exactly the five questions of this lesson."
    )


class RecapAttemptRequest(BaseModel):
    """Submit answers for a recap round (counts towards the streak)."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id (UUID) that owns progress. Temporary until JWT auth.",
    )
    answers: list[AnswerIn] = Field(
        ..., min_length=1, description="Answers for the recap questions that were served."
    )


class AnswerResult(BaseModel):
    """Graded answer with the correct option and explanation."""

    question_id: str
    selected_index: int
    correct_index: int
    correct: bool
    explanation: str | None = None


class AnswerCheckRequest(BaseModel):
    """Check one answer without submitting a whole attempt."""

    selected_index: int = Field(..., ge=0, le=3, description="Chosen option index (0-3).")


class AnswerCheck(BaseModel):
    """Immediate feedback for a single question.

    Correct answers are only revealed here — never in a lesson payload — so the
    learner can only see the answer after committing to one.
    """

    question_id: str
    selected_index: int
    correct_index: int
    correct: bool
    explanation: str | None = None


class AttemptResult(BaseModel):
    """Result of a graded lesson or recap submission."""

    kind: AttemptKind
    lesson_id: str | None = Field(default=None, description="Lesson id; null for recaps.")
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)
    answers: list[AnswerResult]
    streak: StreakRead


class RecapResponse(BaseModel):
    """Five random questions drawn from lessons the user has completed."""

    questions: list[QuestionRead]


class CompletionRead(BaseModel):
    """One completed lesson with its attempt stats."""

    lesson_id: str
    lesson_slug: str
    lesson_title: str
    attempts: int
    last_score: int
    best_score: int
    first_completed_at: datetime | None = None
    last_completed_at: datetime | None = None


class ProgressResponse(BaseModel):
    """The user's completed lessons plus their streak."""

    streak: StreakRead
    completions: list[CompletionRead]
