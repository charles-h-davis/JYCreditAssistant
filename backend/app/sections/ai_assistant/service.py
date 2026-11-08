"""Business logic for the AI Credit Assistant section.

One request = one Gemini call. The model is asked to classify the question and
answer it in a single JSON reply, so scope is enforced server-side:

- Out-of-scope questions never reach the user: the model says ``in_scope: false``
  and we return :data:`REFUSAL_MESSAGE`.
- In-scope answers are returned as-is (the prompt keeps them short and points to
  Credit Learning lessons by exact title).
- An in-scope question with an empty answer falls back to :data:`FALLBACK_MESSAGE`
  rather than an empty bubble.

The lesson catalogue is read from the Credit Learning section's versioned content
so references stay valid without querying its tables.
"""

import logging
from functools import lru_cache
from pathlib import Path

from app.sections.ai_assistant.gemini_client import GeminiClient
from app.sections.ai_assistant.schemas import ChatRequest, ChatResponse
from app.sections.credit_learning.content import CATEGORIES

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"

#: Returned verbatim when the question is outside credit/money topics.
REFUSAL_MESSAGE = "I can't answer that. I can only help with credit and money questions."
#: Returned when the model claims the question is in scope but gives no answer.
FALLBACK_MESSAGE = "I couldn't put together an answer to that. Could you rephrase it?"


@lru_cache(maxsize=1)
def build_lesson_catalogue() -> str:
    """Return the Credit Learning sections and their lessons, as prompt text."""
    lines: list[str] = []
    for category in CATEGORIES:
        lines.append(f"{category.title} (section):")
        lines.extend(
            f"  - {lesson.title} (slug: {lesson.slug})" for lesson in category.lessons
        )
    return "\n".join(lines)


@lru_cache(maxsize=1)
def build_system_prompt() -> str:
    """Return the versioned system prompt plus the current lesson catalogue."""
    base = (PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8").strip()
    return (
        f"{base}\n\n"
        "## Lesson catalogue\n\n"
        "Each entry is a Credit Learning **section** with the lessons it contains.\n"
        "When you point the user at one, always name the lesson *and* its section, "
        "e.g.\n"
        'For more, see the lesson "Statement cycles" in the "Managing Repayments" '
        "section.\n\n"
        f"{build_lesson_catalogue()}\n"
    )


def generate_reply(assistant: GeminiClient, *, request: ChatRequest) -> ChatResponse:
    """Answer `request.message`, refusing anything outside credit topics."""
    question = request.message.strip()
    logger.debug("Assistant question received (%d characters)", len(question))

    result = assistant.answer_question(
        system_prompt=build_system_prompt(), question=question
    )

    if not result["in_scope"]:
        return ChatResponse(
            reply=REFUSAL_MESSAGE,
            in_scope=False,
            refused=True,
            model=getattr(assistant, "model", None),
        )

    answer = (result.get("answer") or "").strip()
    if not answer:
        return ChatResponse(
            reply=FALLBACK_MESSAGE,
            in_scope=True,
            refused=True,
            model=getattr(assistant, "model", None),
        )

    return ChatResponse(
        reply=answer,
        in_scope=True,
        refused=False,
        model=getattr(assistant, "model", None),
    )

