"""HTTP routes for the AI Credit Assistant (mounted at /api/v1/ai-assistant)."""

from fastapi import APIRouter, Depends

from app.sections.ai_assistant import service
from app.sections.ai_assistant.gemini_client import GeminiClient, get_gemini_client
from app.sections.ai_assistant.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai-assistant", tags=["AI Credit Assistant"])


@router.get("/ping", summary="Health check for the AI Credit Assistant section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "ai-assistant", "status": "ok"}


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a credit question",
    responses={
        422: {"description": "Missing, blank or oversized message."},
        502: {"description": "Gemini rejected the request or returned bad data."},
        503: {"description": "GEMINI_API_KEY is not configured (see backend/.env)."},
    },
)
def chat(
    payload: ChatRequest,
    gemini: GeminiClient = Depends(get_gemini_client),
) -> ChatResponse:
    """Answer a credit/money question in plain terms; refuse anything off-topic.

    The model classifies the question in the same call that answers it. Off-topic
    questions return the fixed refusal with ``in_scope=false`` and ``refused=true``;
    in-scope answers can point to a Credit Learning lesson by title.
    """
    return service.generate_reply(gemini, request=payload)
