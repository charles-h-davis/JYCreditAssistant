"""Smoke tests for the Credit Learning section.

Owner: credit_learning. Extend this file as lessons get implemented.
"""

from fastapi.testclient import TestClient

SECTION = "credit-learning"


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_list_lessons_is_not_implemented_yet(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/lessons")

    assert response.status_code == 501


def test_get_lesson_is_not_implemented_yet(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/lessons/how-apr-works")

    assert response.status_code == 501
