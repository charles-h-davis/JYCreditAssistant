"""AI Credit Assistant section.

Conversational help for credit questions: explains a user's own numbers in plain
language, suggests payoff strategies and points back to Credit Learning content.

Guardrails live in `prompts/system_prompt.md` — educational guidance only, never
regulated financial advice.

Owner: _fill in_
"""

from app.sections.ai_assistant.router import router

__all__ = ["router"]
