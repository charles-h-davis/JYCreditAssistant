"""Business logic for the AI Credit Assistant section.

TODO(ai_assistant owner):
  - `generate_reply(client, user_id, request)` -> persist the turn, call the model
    with `build_system_prompt()`, return `ChatResponse`.
  - Keep the model call behind a thin function so it can be swapped/mocked.
  - Ground answers in the user's own cards (read them through the Card Storage
    section's service, not by querying `credit_cards` here).
"""

from functools import lru_cache
from pathlib import Path

from supabase import Client

from app.sections.ai_assistant.schemas import ChatRequest, ChatResponse

PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache(maxsize=1)
def build_system_prompt() -> str:
    """Return the assistant's system prompt from `prompts/system_prompt.md`."""
    return (PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8").strip()


def generate_reply(client: Client, *, user_id: str, request: ChatRequest) -> ChatResponse:
    """Answer `request.message` for `user_id`, persisting the conversation."""
    raise NotImplementedError("TODO(ai_assistant): implement generate_reply")
