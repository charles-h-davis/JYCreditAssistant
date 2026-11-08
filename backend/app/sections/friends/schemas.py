"""Request/response models for the Friends section.

A friend is a contact row the user owns (`friend_name` + `friend_email`), not a
Supabase auth user, so the only thing the browser sends is an email address.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Deliberately loose: `something@something.something`. Pydantic's `EmailStr`
#: would need the `email-validator` package, which is not a dependency yet.
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class FriendRead(BaseModel):
    """One friend in the caller's list."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Friend row id (UUID).")
    user_id: str = Field(..., description="Owner of the friend list.")
    friend_name: str = Field(
        ..., description="Display name; derived from the email when not supplied."
    )
    friend_email: str = Field(..., description="Lower-cased email address.")
    created_at: datetime | None = Field(default=None, description="When they were added (UTC).")


class FriendCreate(BaseModel):
    """Add a friend by email."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the friend list. Temporary until JWT auth.",
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=254,
        pattern=EMAIL_PATTERN,
        description="Friend's email address. Stored trimmed and lower-cased.",
    )
    name: str | None = Field(
        default=None,
        max_length=80,
        description="Optional display name; derived from the email when omitted.",
    )

    @field_validator("email", mode="before")
    @classmethod
    def _strip_email(cls, value: object) -> object:
        """Trim before the pattern runs, so a pasted padded address still validates."""
        return value.strip() if isinstance(value, str) else value
