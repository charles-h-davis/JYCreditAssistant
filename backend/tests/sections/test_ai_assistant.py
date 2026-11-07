"""Smoke tests for the AI Credit Assistant section.

Owner: ai_assistant. Extend this file as chat gets implemented.
"""

from fastapi.testclient import TestClient

SECTION = "ai-assistant"


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_chat_rejects_empty_message(client: TestClient, api_prefix: str) -> None:
    response = client.post(f"{api_prefix}/{SECTION}/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_is_not_implemented_yet(client: TestClient, api_prefix: str) -> None:
    response = client.post(f"{api_prefix}/{SECTION}/chat", json={"message": "What is APR?"})

    assert response.status_code == 501


def test_system_prompt_is_versioned_and_loads() -> None:
    """The prompt file is part of the section's contract; it must exist and be non-trivial."""
    from app.sections.ai_assistant.service import build_system_prompt

    prompt = build_system_prompt()

    assert "guardrail" in prompt.lower() or "never" in prompt.lower()
    assert len(prompt) > 500
