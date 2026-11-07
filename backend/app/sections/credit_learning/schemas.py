"""Request/response models for the Credit Learning section."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["beginner", "intermediate", "advanced"]


class LessonSummary(BaseModel):
    """Card-sized view of a lesson, used by the lesson list screen."""

    model_config = ConfigDict(from_attributes=True)

    slug: str = Field(..., description="URL-safe identifier, e.g. 'how-apr-works'.")
    title: str = Field(..., description="Human-readable lesson title.")
    summary: str = Field(..., description="One or two sentences describing the lesson.")
    difficulty: Difficulty = Field(..., description="Target audience level.")
    estimated_minutes: int = Field(..., gt=0, description="Rough reading time in minutes.")


class LessonDetail(LessonSummary):
    """A full lesson, including body copy and takeaways."""

    body_markdown: str = Field(..., description="Lesson body, rendered from Markdown.")
    key_takeaways: list[str] = Field(
        default_factory=list, description="Three or so one-line takeaways."
    )
    updated_at: datetime | None = Field(default=None, description="Last content update (UTC).")
