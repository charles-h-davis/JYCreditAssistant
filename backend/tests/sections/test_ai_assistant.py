"""Tests for the AI Credit Assistant section.

Credential-free: the Gemini dependency is replaced with a fake, and the REST
response parsing is exercised from canned payloads.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.exceptions import UpstreamServiceError
from app.main import app
from app.sections.ai_assistant import service
from app.sections.ai_assistant.gemini_client import (
    get_gemini_client,
    parse_reply,
)

SECTION = "ai-assistant"


class FakeGeminiClient:
    """Stand-in for `GeminiClient` returning a canned classification."""

    def __init__(
        self,
        *,
        in_scope: bool = True,
        answer: str = "Pay the **highest APR** first.",
        error: Exception | None = None,
        model: str = "gemini-test",
    ) -> None:
        self.model = model
        self.in_scope = in_scope
        self.answer = answer
        self.error = error
        self.calls: list[dict[str, str]] = []

    def answer_question(
        self, *, system_prompt: str, question: str
    ) -> dict[str, Any]:
        self.calls.append({"system_prompt": system_prompt, "question": question})
        if self.error is not None:
            raise self.error
        return {"in_scope": self.in_scope, "answer": self.answer}


@pytest.fixture(autouse=True)
def offline_gemini() -> Iterator[None]:
    """Keep endpoint tests offline with a default fake Gemini client."""
    app.dependency_overrides[get_gemini_client] = lambda: FakeGeminiClient()
    yield
    app.dependency_overrides.clear()


def _use_gemini(fake: FakeGeminiClient) -> None:
    """Swap in a specific fake for one test."""
    app.dependency_overrides[get_gemini_client] = lambda: fake


def _chat_url(api_prefix: str) -> str:
    return f"{api_prefix}/{SECTION}/chat"


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_chat_rejects_empty_message(client: TestClient, api_prefix: str) -> None:
    response = client.post(_chat_url(api_prefix), json={"message": ""})

    assert response.status_code == 422


def test_chat_rejects_whitespace_only_message(
    client: TestClient, api_prefix: str
) -> None:
    response = client.post(_chat_url(api_prefix), json={"message": "   "})

    assert response.status_code == 422


def test_chat_rejects_oversized_message(
    client: TestClient, api_prefix: str
) -> None:
    response = client.post(_chat_url(api_prefix), json={"message": "a" * 2001})

    assert response.status_code == 422


def test_chat_answers_in_scope_question(
    client: TestClient, api_prefix: str
) -> None:
    fake = FakeGeminiClient(
        answer=(
            "Pay the **highest APR** card first to save the most interest.\n"
            'For more, see the lesson "Interest and APR".'
        )
    )
    _use_gemini(fake)

    response = client.post(
        _chat_url(api_prefix),
        json={"message": "  Should I pay off my highest APR card first?  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["in_scope"] is True
    assert body["refused"] is False
    assert body["model"] == "gemini-test"
    assert "**highest APR**" in body["reply"]

    # The question is trimmed and the prompt carries the lesson catalogue.
    assert fake.calls[0]["question"] == "Should I pay off my highest APR card first?"
    prompt = fake.calls[0]["system_prompt"]
    assert "Lesson catalogue" in prompt
    assert "What credit is and how it works" in prompt
    assert "in_scope" in prompt


def test_chat_refuses_out_of_scope_question(
    client: TestClient, api_prefix: str
) -> None:
    fake = FakeGeminiClient(in_scope=False, answer="This must never be shown.")
    _use_gemini(fake)

    response = client.post(
        _chat_url(api_prefix), json={"message": "Who won the 2022 World Cup?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == service.REFUSAL_MESSAGE
    assert body["in_scope"] is False
    assert body["refused"] is True


def test_chat_falls_back_when_in_scope_answer_is_empty(
    client: TestClient, api_prefix: str
) -> None:
    _use_gemini(FakeGeminiClient(in_scope=True, answer="   "))

    response = client.post(
        _chat_url(api_prefix), json={"message": "What is a credit score?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == service.FALLBACK_MESSAGE
    assert body["in_scope"] is True
    assert body["refused"] is True


def test_chat_maps_gemini_failures_to_502(
    client: TestClient, api_prefix: str
) -> None:
    _use_gemini(FakeGeminiClient(error=UpstreamServiceError("Gemini exploded")))

    response = client.post(
        _chat_url(api_prefix), json={"message": "What is APR?"}
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_error"


def test_chat_returns_503_without_gemini_key(
    client: TestClient, api_prefix: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    app.dependency_overrides.pop(get_gemini_client, None)
    monkeypatch.setattr(settings, "gemini_api_key", "")

    response = client.post(_chat_url(api_prefix), json={"message": "What is APR?"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "gemini_not_configured"


# --- Gemini reply parsing ---------------------------------------------------


def _gemini_payload(text: str) -> dict[str, Any]:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_parse_reply_reads_in_scope_answer() -> None:
    result = parse_reply(_gemini_payload('{"in_scope": true, "answer": " Pay more. "}'))

    assert result == {"in_scope": True, "answer": "Pay more."}


def test_parse_reply_strips_markdown_code_fence() -> None:
    text = '```json\n{"in_scope": false, "answer": ""}\n```'

    assert parse_reply(_gemini_payload(text)) == {"in_scope": False, "answer": ""}


def test_parse_reply_rejects_missing_candidates() -> None:
    with pytest.raises(UpstreamServiceError):
        parse_reply({})


def test_parse_reply_rejects_non_json_text() -> None:
    with pytest.raises(UpstreamServiceError):
        parse_reply(_gemini_payload("Sure! APR stands for..."))


def test_parse_reply_rejects_wrong_shape() -> None:
    with pytest.raises(UpstreamServiceError):
        parse_reply(_gemini_payload('{"in_scope": "yes", "answer": ""}'))


# --- system prompt ----------------------------------------------------------


def test_system_prompt_includes_scope_rules_and_lesson_catalogue() -> None:
    prompt = service.build_system_prompt().lower()

    assert "guardrail" in prompt
    assert "never" in prompt
    assert "out of scope" in prompt
    assert "in_scope" in prompt
    assert "lesson catalogue" in prompt
    assert "what credit is and how it works" in prompt
    assert "what-credit-is" in prompt
    # References must name the section as well as the lesson.
    assert "credit basics (section)" in prompt
    assert "in the \"<exact section>\" section".lower() in prompt
    assert len(prompt) > 1500
