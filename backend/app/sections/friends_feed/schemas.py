"""Request/response models for the Friends Feed section.

The friend events are hardcoded server-side, so the only thing the browser sends
is the outcome of an attempt it just had graded (see ``FeedEntryCreate``).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FeedKind = Literal["lesson", "recap", "streak"]
RecordableKind = Literal["lesson", "recap"]


class FeedEntry(BaseModel):
    """One activity row in the feed."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Entry id: a fixture id, or the stored row's UUID.")
    actor: str = Field(
        ..., description="Who the activity belongs to. Always 'You' for the caller's own rows."
    )
    kind: FeedKind = Field(
        ..., description="Kind of activity: a finished lesson, a refresh round, or a streak."
    )
    action: str = Field(
        ...,
        description="What happened, e.g. 'completed Financial Arithmetic — Interest and APR'.",
    )
    detail: str | None = Field(
        default=None, description="Optional qualifier shown under the action, e.g. '4/5 correct'."
    )
    occurred_at: datetime = Field(..., description="When it happened (UTC, ISO 8601).")
    is_self: bool = Field(..., description="True when this is the caller's own activity.")


class FriendsFeedResponse(BaseModel):
    """The merged feed, newest first and already cut to the requested size."""

    entries: list[FeedEntry]


class FeedEntryCreate(BaseModel):
    """Record one finished lesson or refresh round in the caller's feed.

    The client sends what the grader just returned; the API owns the wording of
    the feed row, so presentation never comes from the browser.
    """

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the entry. Temporary until JWT auth.",
    )
    kind: RecordableKind = Field(
        ..., description="'lesson' for a finished lesson, 'recap' for a refresh round."
    )
    lesson_title: str | None = Field(
        default=None,
        max_length=120,
        description="Lesson title. Required when kind='lesson'; ignored for recaps.",
    )
    score: int = Field(..., ge=0, description="Questions answered correctly in this attempt.")
    total: int = Field(..., ge=1, description="Questions in this attempt.")

    @model_validator(mode="after")
    def _check_attempt(self) -> "FeedEntryCreate":
        """Reject impossible attempts and a lesson entry with no title."""
        if self.score > self.total:
            msg = "score cannot be greater than total."
            raise ValueError(msg)
        if self.kind == "lesson" and not (self.lesson_title or "").strip():
            msg = "lesson_title is required for a lesson entry."
            raise ValueError(msg)
        return self
