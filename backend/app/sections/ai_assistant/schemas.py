"""Request/response models for the AI Credit Assistant section."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    """One turn in a conversation."""

    role: ChatRole = Field(..., description="Who produced this message.")
    content: str = Field(..., min_length=1, description="Message text.")


class ChatRequest(BaseModel):
    """A user question for the assistant."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Is it better to pay off my highest APR card first?",
                "conversation_id": "b0e1c2d3-4567-89ab-cdef-0123456789ab",
            }
        }
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question. Plain text; never include card numbers or SSNs.",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation to continue. Omit to start a new one.",
    )


class ChatResponse(BaseModel):
    """The assistant's reply plus conversation bookkeeping."""

    conversation_id: str = Field(..., description="Conversation this reply belongs to.")
    reply: str = Field(..., description="Assistant answer, Markdown allowed.")
    model: str | None = Field(default=None, description="Model that produced the reply.")
    suggestions: list[str] = Field(
        default_factory=list, description="Follow-up prompts the UI can offer."
    )
    created_at: datetime | None = Field(default=None, description="Reply timestamp (UTC).")
