"""Smoke tests for the Cost to Buy section.

Owner: cost_to_buy. Extend this file as the estimate endpoint gets implemented.
"""

from fastapi.testclient import TestClient

SECTION = "cost-to-buy"


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_estimate_rejects_invalid_amount(client: TestClient, api_prefix: str) -> None:
    payload = {"purchase_amount": 0, "apr": 24.99}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 422


def test_estimate_rejects_out_of_range_apr(client: TestClient, api_prefix: str) -> None:
    payload = {"purchase_amount": 500, "apr": 140}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 422


def test_estimate_is_not_implemented_yet(client: TestClient, api_prefix: str) -> None:
    payload = {"purchase_amount": 1200.0, "apr": 24.99, "monthly_payment": 150.0}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 501
