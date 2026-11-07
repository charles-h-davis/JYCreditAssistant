"""Smoke tests for the Card Storage section.

Owner: card_storage. Extend this file as cards get implemented.
"""

from fastapi.testclient import TestClient

SECTION = "card-storage"

VALID_CARD = {
    "nickname": "Everyday card",
    "issuer": "Chase",
    "last_four": "4321",
    "credit_limit": 5000.0,
    "current_balance": 1875.4,
    "apr": 24.99,
    "statement_day": 12,
    "due_day": 5,
}


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_create_card_rejects_full_pan(client: TestClient, api_prefix: str) -> None:
    """`last_four` must be exactly four digits — no full card numbers."""
    payload = {**VALID_CARD, "last_four": "4321123456789012"}

    response = client.post(f"{api_prefix}/{SECTION}/cards", json=payload)

    assert response.status_code == 422


def test_create_card_rejects_invalid_day(client: TestClient, api_prefix: str) -> None:
    payload = {**VALID_CARD, "due_day": 32}

    response = client.post(f"{api_prefix}/{SECTION}/cards", json=payload)

    assert response.status_code == 422


def test_create_card_is_not_implemented_yet(client: TestClient, api_prefix: str) -> None:
    response = client.post(f"{api_prefix}/{SECTION}/cards", json=VALID_CARD)

    assert response.status_code == 501
