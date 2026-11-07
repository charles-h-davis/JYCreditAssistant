"""HTTP routes for the AI Credit Assistant (mounted at /api/v1/ai-assistant)."""

from fastapi import APIRouter, HTTPException, status

from app.sections.ai_assistant.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai-assistant", tags=["AI Credit Assistant"])

NOT_IMPLEMENTED = {
    status.HTTP_501_NOT_IMPLEMENTED: {"description": "Not implemented yet (scaffold stub)."}
}


@router.get("/ping", summary="Health check for the AI Credit Assistant section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "ai-assistant", "status": "ok"}


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the credit assistant a question",
    responses={
        422: {"description": "Invalid chat payload."},
        **NOT_IMPLEMENTED,
    },
)
def chat(payload: ChatRequest) -> ChatResponse:
    """Answer a credit question using the versioned system prompt.

    TODO(ai_assistant owner): call `service.generate_reply(...)`; it must load
    `prompts/system_prompt.md` via `service.build_system_prompt()` and persist the
    turn to `chat_messages`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ai_assistant.chat is not implemented yet.",
    )
