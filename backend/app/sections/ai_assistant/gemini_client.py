"""Thin synchronous client for Gemini's text ``generateContent`` call.

The assistant asks Gemini one question at a time and expects a JSON reply
``{"in_scope": bool, "answer": str}``. We call the REST API over plain HTTPS
(`httpx`) instead of adding a SDK dependency; calls are synchronous so the route
stays plain ``def`` and FastAPI runs it in its threadpool.

Credentials come from ``app.core.config.settings`` (``GEMINI_API_KEY`` in
``backend/.env``). The key is sent as an ``x-goog-api-key`` header, never in the
query string, so it cannot leak into httpx INFO logs. No network I/O at import.
"""

import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AppError, UpstreamServiceError

logger = logging.getLogger(__name__)

#: Gemini REST host. ``v1beta`` exposes ``models/{model}:generateContent``.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
REQUEST_TIMEOUT_SECONDS = 30.0
TEMPERATURE = 0.4
#: Keep answers concise (roughly 120 words) even if the prompt is ignored.
MAX_OUTPUT_TOKENS = 512

#: The exact shape we ask Gemini to return, enforced via responseSchema.
REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "in_scope": {"type": "boolean"},
        "answer": {"type": "string"},
    },
    "required": ["in_scope", "answer"],
}


class GeminiNotConfiguredError(AppError):
    """Raised when the Gemini API key is missing from the environment."""

    status_code = 503
    code = "gemini_not_configured"
    message = (
        "The AI assistant is not configured. Set GEMINI_API_KEY in backend/.env "
        "(see .env.example)."
    )


def _strip_code_fence(text: str) -> str:
    """Drop a surrounding ```json fence if the model added one anyway."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = [
        line for line in stripped.splitlines() if not line.strip().startswith("```")
    ]
    return "\n".join(lines).strip()


def parse_reply(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate Gemini's JSON reply into ``{"in_scope": bool, "answer": str}``."""
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise UpstreamServiceError(
            "Gemini returned an unexpected response shape."
        ) from exc

    text = _strip_code_fence("".join(part.get("text", "") for part in parts))
    if not text:
        raise UpstreamServiceError("Gemini returned an empty reply.")
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise UpstreamServiceError("Gemini did not return valid JSON.") from exc
    if not isinstance(data, dict):
        raise UpstreamServiceError("Gemini did not return a JSON object.")

    in_scope = data.get("in_scope")
    answer = data.get("answer")
    if not isinstance(in_scope, bool) or not isinstance(answer, str):
        raise UpstreamServiceError("Gemini reply is missing 'in_scope' or 'answer'.")
    return {"in_scope": in_scope, "answer": answer.strip()}


class GeminiClient:
    """Minimal text-only Gemini wrapper for the credit assistant."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = (base_url or GEMINI_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.timeout = timeout

    def answer_question(
        self, *, system_prompt: str, question: str
    ) -> dict[str, Any]:
        """Classify and answer `question`; returns ``{"in_scope", "answer"}``."""
        url = f"{self.base_url}/models/{self.model}:generateContent"
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": question}]}],
            "generationConfig": {
                "temperature": TEMPERATURE,
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
                "responseMimeType": "application/json",
                "responseSchema": REPLY_SCHEMA,
            },
        }
        headers = {"x-goog-api-key": self.api_key}
        try:
            with httpx.Client(timeout=self.timeout) as http_client:
                response = http_client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise UpstreamServiceError(f"Gemini request failed: {exc}") from exc

        if response.status_code >= 400:
            try:
                message = (
                    ((response.json().get("error") or {}).get("message") or "")[:200]
                )
            except ValueError:
                message = response.text[:200]
            logger.warning(
                "Gemini chat failed: HTTP %s (%s)", response.status_code, message
            )
            raise UpstreamServiceError(
                f"Gemini returned HTTP {response.status_code}: {message}"
            )

        return parse_reply(response.json())


def get_gemini_client() -> GeminiClient:
    """FastAPI dependency: a configured Gemini client, or 503 when key is missing."""
    if not settings.gemini_api_key:
        raise GeminiNotConfiguredError()
    return GeminiClient()
