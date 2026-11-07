"""Tests for the Cost to Buy section.

The suite must pass without Supabase or Gemini credentials: the database client and
the Gemini client are overridden with in-memory fakes, and the amortisation maths is
exercised directly (it is pure).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_supabase_admin
from app.main import app
from app.sections.cost_to_buy import repository, service
from app.sections.cost_to_buy.gemini_client import get_gemini_client

SECTION = "cost-to-buy"
USER_ID = "11111111-1111-1111-1111-111111111111"
CARD_ID = "22222222-2222-2222-2222-222222222222"

IMAGE_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 32


class FakeGeminiClient:
    """Stand-in for `GeminiClient` returning a fixed extraction payload."""

    def __init__(
        self, payload: dict[str, Any] | None = None, *, model: str = "fake-gemini"
    ) -> None:
        self.model = model
        self.payload = payload or {
            "product_name": "Running shoes",
            "price": 119.99,
            "currency": "GBP",
            "raw_text": "RUNNING SHOES 119.99",
            "confidence": 0.92,
        }

    def extract_json(
        self, *, image_bytes: bytes, mime_type: str, prompt: str
    ) -> dict[str, Any]:
        return self.payload


class FakeRepository:
    """In-memory stand-in for the repository module."""

    def __init__(self) -> None:
        self.plans: dict[str, dict[str, Any]] = {}
        self.payments: dict[tuple[str, str], dict[str, Any]] = {}
        self._next = 0

    def list_purchase_plans(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        return [row for row in self.plans.values() if row["user_id"] == user_id]

    def insert_purchase_plan(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._next += 1
        row = {
            "id": f"plan-{self._next}",
            "user_id": user_id,
            "created_at": "2026-07-11T00:00:00+00:00",
            **payload,
        }
        self.plans[row["id"]] = row
        return row

    def get_monthly_payment(
        self, client: Any, *, user_id: str, card_id: str
    ) -> dict[str, Any] | None:
        return self.payments.get((user_id, card_id))

    def upsert_monthly_payment(
        self, client: Any, *, user_id: str, card_id: str, monthly_payment: float
    ) -> dict[str, Any]:
        row = {
            "user_id": user_id,
            "card_id": card_id,
            "monthly_payment": monthly_payment,
            "updated_at": "2026-07-11T00:00:00+00:00",
        }
        self.payments[(user_id, card_id)] = row
        return row


@pytest.fixture(autouse=True)
def offline_dependencies() -> Iterator[None]:
    """Keep endpoint tests offline: fake DB client and fake Gemini client."""
    app.dependency_overrides[get_supabase_admin] = lambda: object()
    app.dependency_overrides[get_gemini_client] = lambda: FakeGeminiClient()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> FakeRepository:
    """Replace every repository call with an in-memory store."""
    fake = FakeRepository()
    for name in (
        "list_purchase_plans",
        "insert_purchase_plan",
        "get_monthly_payment",
        "upsert_monthly_payment",
    ):
        monkeypatch.setattr(repository, name, getattr(fake, name))
    return fake


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


# --- estimate --------------------------------------------------------------


def test_estimate_rejects_invalid_amount(client: TestClient, api_prefix: str) -> None:
    payload = {"purchase_amount": 0, "purchase_apr": 24.99}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 422


def test_estimate_rejects_out_of_range_apr(client: TestClient, api_prefix: str) -> None:
    payload = {"purchase_amount": 500, "purchase_apr": 140}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 422


def test_estimate_returns_amortisation(client: TestClient, api_prefix: str) -> None:
    payload = {
        "purchase_amount": 1200.0,
        "purchase_apr": 24.99,
        "monthly_payment": 150.0,
        "closing_day": 12,
        "statement_day": 5,
    }

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert 8 <= body["months_to_payoff"] <= 12
    assert body["total_interest"] > 0
    assert body["total_paid"] == round(1200.0 + body["total_interest"], 2)
    assert body["payoff_date"] is not None


def test_estimate_zero_apr_has_no_interest(client: TestClient, api_prefix: str) -> None:
    payload = {"purchase_amount": 1200.0, "purchase_apr": 0, "monthly_payment": 100.0}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["total_interest"] == 0.0
    assert body["months_to_payoff"] == 12


def test_estimate_rejects_payment_below_interest(
    client: TestClient, api_prefix: str
) -> None:
    payload = {"purchase_amount": 5000.0, "purchase_apr": 30, "monthly_payment": 50.0}

    response = client.post(f"{api_prefix}/{SECTION}/estimate", json=payload)

    assert response.status_code == 422


# --- purchase impact -------------------------------------------------------


def test_purchase_impact_returns_extra_cost(client: TestClient, api_prefix: str) -> None:
    payload = {
        "current_balance": 1800.0,
        "purchase_apr": 24.99,
        "purchase_amount": 120.0,
        "current_monthly_payment": 150.0,
        "closing_day": 12,
        "statement_day": 5,
    }

    response = client.post(f"{api_prefix}/{SECTION}/purchase-impact", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["extra_total_paid"] > 0
    # Extra total paid is the item itself plus the extra interest.
    assert body["extra_total_paid"] >= 120.0
    assert len(body["scenarios"]) > 0
    assert (
        body["with_purchase"]["months_to_payoff"] >= body["baseline"]["months_to_payoff"]
    )


def test_purchase_impact_rejects_payment_below_interest(
    client: TestClient, api_prefix: str
) -> None:
    payload = {
        "current_balance": 8000.0,
        "purchase_apr": 30,
        "purchase_amount": 100.0,
        "current_monthly_payment": 50.0,
        "closing_day": 12,
        "statement_day": 5,
    }

    response = client.post(f"{api_prefix}/{SECTION}/purchase-impact", json=payload)

    assert response.status_code == 422


# --- extract ---------------------------------------------------------------


def test_extract_returns_parsed_product(client: TestClient, api_prefix: str) -> None:
    files = {"file": ("tag.png", IMAGE_BYTES, "image/png")}

    response = client.post(f"{api_prefix}/{SECTION}/extract", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["product_name"] == "Running shoes"
    assert body["price"] == 119.99
    assert body["currency"] == "GBP"


def test_extract_rejects_non_image(client: TestClient, api_prefix: str) -> None:
    files = {"file": ("notes.txt", b"hello", "text/plain")}

    response = client.post(f"{api_prefix}/{SECTION}/extract", files=files)

    assert response.status_code == 415


def test_extract_rejects_missing_file(client: TestClient, api_prefix: str) -> None:
    response = client.post(f"{api_prefix}/{SECTION}/extract")

    assert response.status_code == 422


def test_extract_returns_503_without_gemini_credentials(
    client: TestClient, api_prefix: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    app.dependency_overrides.pop(get_gemini_client, None)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    files = {"file": ("tag.png", IMAGE_BYTES, "image/png")}

    response = client.post(f"{api_prefix}/{SECTION}/extract", files=files)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "gemini_not_configured"


# --- pure helpers ----------------------------------------------------------


def test_parse_extraction_payload_handles_missing_price() -> None:
    result = service.parse_extraction_payload(
        {"product_name": "Mug", "price": None, "currency": "GBP"}, model="m"
    )

    assert result.product_name == "Mug"
    assert result.price is None
    assert result.model == "m"


def test_parse_extraction_payload_coerces_numeric_strings() -> None:
    result = service.parse_extraction_payload(
        {"product_name": "Mug", "price": "12.50", "currency": "GBP"}
    )

    assert result.price == 12.5


def test_amortize_zero_balance_is_immediate() -> None:
    summary = service.amortize(0.0, 24.99, 100.0)

    assert summary.months_to_payoff == 0
    assert summary.total_interest == 0.0


def test_amortize_rejects_unpayable_payment() -> None:
    with pytest.raises(ValueError):
        service.amortize(5000.0, 30.0, 50.0)


def test_suggest_payment_clears_in_horizon() -> None:
    payment = service.suggest_payment(1200.0, 24.99, months=24)

    summary = service.amortize(1200.0, 24.99, payment)

    assert summary.months_to_payoff <= 24


# --- persistence -----------------------------------------------------------


def test_create_purchase_plan_sets_payment(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    payload = {
        "user_id": USER_ID,
        "card_id": CARD_ID,
        "product_name": "Running shoes",
        "purchase_amount": 120.0,
        "monthly_payment": 175.0,
        "months_to_payoff": 15,
        "total_interest": 42.0,
    }

    response = client.post(f"{api_prefix}/{SECTION}/purchase-plans", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["product_name"] == "Running shoes"
    assert body["purchase_amount"] == 120.0
    # Confirming the purchase also updates the stored monthly payment.
    assert store.payments[(USER_ID, CARD_ID)]["monthly_payment"] == 175.0


def test_list_purchase_plans(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    client.post(
        f"{api_prefix}/{SECTION}/purchase-plans",
        json={
            "user_id": USER_ID,
            "card_id": CARD_ID,
            "purchase_amount": 50.0,
            "monthly_payment": 160.0,
        },
    )

    response = client.get(
        f"{api_prefix}/{SECTION}/purchase-plans", params={"user_id": USER_ID}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_monthly_payment_404_when_missing(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.get(
        f"{api_prefix}/{SECTION}/monthly-payment",
        params={"user_id": USER_ID, "card_id": CARD_ID},
    )

    assert response.status_code == 404


def test_put_monthly_payment_roundtrip(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    put = client.put(
        f"{api_prefix}/{SECTION}/monthly-payment",
        json={"user_id": USER_ID, "card_id": CARD_ID, "monthly_payment": 200.0},
    )

    assert put.status_code == 200
    assert put.json()["monthly_payment"] == 200.0

    get = client.get(
        f"{api_prefix}/{SECTION}/monthly-payment",
        params={"user_id": USER_ID, "card_id": CARD_ID},
    )

    assert get.status_code == 200
    assert get.json()["monthly_payment"] == 200.0
