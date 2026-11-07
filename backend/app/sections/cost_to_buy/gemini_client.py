"""Thin synchronous client for the Gemini REST API (vision extraction).

The Cost to Buy section asks Gemini to read a product name and price out of a
photo of a price tag or a product screenshot. We call the REST API over plain
HTTPS (`httpx`) instead of adding the `google-genai` dependency. Calls are
synchronous so routes stay plain ``def`` and FastAPI runs them in its threadpool —
never block the event loop with these.

Credentials come from ``app.core.config.settings`` (loaded from ``backend/.env``).
No network I/O happens at import time.
"""

import base64
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


class GeminiNotConfiguredError(AppError):
    """Raised when the Gemini API key is missing from the environment."""

    status_code = 503
    code = "gemini_not_configured"
    message = (
        "Gemini is not configured. Set GEMINI_API_KEY in backend/.env "
        "(see .env.example)."
    )


class GeminiClient:
    """Minimal Gemini API wrapper (only the vision call this section needs)."""

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

    def extract_json(
        self, *, image_bytes: bytes, mime_type: str, prompt: str
    ) -> dict[str, Any]:
        """Send one image + prompt to Gemini and return the parsed JSON reply.

        The model is asked (via ``responseMimeType``) to answer with a single JSON
        object; anything else raises ``UpstreamServiceError`` so callers never get
        half-parsed data.
        """
        url = f"{self.base_url}/models/{self.model}:generateContent"
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        # Send the key as a header, never as a `?key=` query param: httpx logs the
        # full request URL at INFO level, which would leak the key into server logs.
        headers = {"x-goog-api-key": self.api_key}
        try:
            with httpx.Client(timeout=self.timeout) as http_client:
                response = http_client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise UpstreamServiceError(f"Gemini request failed: {exc}") from exc

        if response.status_code >= 400:
            logger.warning(
                "Gemini generateContent failed: HTTP %s (%s)",
                response.status_code,
                response.text[:200],
            )
            raise UpstreamServiceError(f"Gemini returned HTTP {response.status_code}.")

        return self._parse_response(response.json())

    @staticmethod
    def _parse_response(payload: dict[str, Any]) -> dict[str, Any]:
        """Pull the JSON object out of a Gemini ``generateContent`` response."""
        try:
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UpstreamServiceError(
                "Gemini returned an unexpected response shape."
            ) from exc
        try:
            data = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise UpstreamServiceError("Gemini did not return valid JSON.") from exc
        if not isinstance(data, dict):
            raise UpstreamServiceError("Gemini did not return a JSON object.")
        return data


def get_gemini_client() -> GeminiClient:
    """FastAPI dependency: a configured Gemini client, or 503 when key is missing."""
    if not settings.gemini_api_key:
        raise GeminiNotConfiguredError()
    return GeminiClient()
