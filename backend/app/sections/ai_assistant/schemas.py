"""Request/response models for the AI Credit Assistant section.

The assistant is scope-limited: replies carry `in_scope`/`refused` so the frontend
can present an off-topic refusal distinctly from a real answer.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

#: A trimmed question between 1 and 2000 characters.
QuestionText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]


class ChatRequest(BaseModel):
    """A user question for the assistant."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Is it better to pay off my highest APR card first?",
            }
        }
    )

    message: QuestionText = Field(
        ...,
        description=(
            "The user's question. Plain text; never include card numbers, CVVs or SSNs."
        ),
    )


class ChatResponse(BaseModel):
    """The assistant's reply and whether the question was in scope."""

    reply: str = Field(..., description="Assistant answer in plain language (Markdown allowed).")
    in_scope: bool = Field(
        ...,
        description="False when the question was outside credit and money topics.",
    )
    refused: bool = Field(
        ..., description="True when the assistant declined to answer."
    )
    model: str | None = Field(
        default=None, description="Gemini model that produced the reply."
    )

