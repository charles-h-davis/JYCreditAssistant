"""Tests for the Notifications section.

Credential-free: the Supabase dependency is overridden and the repository module is
replaced with an in-memory fake.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_supabase_admin
from app.main import app
from app.sections.notifications import repository, service

SECTION = "notifications"
USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"
CARD_ID = "card-one"
OTHER_CARD_ID = "card-two"

TODAY = date(2026, 11, 8)


def _plan(
    *,
    plan_id: str = "plan-1",
    amount: float = 249.99,
    card_id: str = CARD_ID,
    created_at: datetime | None = None,
    product_name: str | None = "Sony WH-1000XM5",
) -> dict[str, Any]:
    return {
        "id": plan_id,
        "user_id": USER_ID,
        "card_id": card_id,
        "product_name": product_name,
        "purchase_amount": amount,
        "created_at": (created_at or datetime(2026, 11, 8, 10, 12, tzinfo=UTC)).isoformat(),
    }


def _transaction(
    *,
    transaction_id: str = "txn-1",
    amount: float = 249.99,
    card_id: str = CARD_ID,
    authorized_date: date | None = TODAY,
    merchant_name: str | None = "Argos",
) -> dict[str, Any]:
    return {
        "id": transaction_id,
        "user_id": USER_ID,
        "card_id": card_id,
        "amount": amount,
        "description": "ARGOS RETAIL LTD",
        "merchant_name": merchant_name,
        "authorized_date": authorized_date.isoformat() if authorized_date else None,
        "posted_date": None,
        "pending": False,
    }


class FakeRepository:
    """In-memory stand-in for `repository`."""

    def __init__(self) -> None:
        self.plans: list[dict[str, Any]] = []
        self.transactions: list[dict[str, Any]] = []
        self.dismissals: list[dict[str, Any]] = []

    def list_purchase_plans(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        return [row for row in self.plans if row["user_id"] == user_id]

    def list_transactions(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        return [row for row in self.transactions if row["user_id"] == user_id]

    def list_dismissals(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        return [row for row in self.dismissals if row["user_id"] == user_id]

    def insert_dismissal(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        existing = next(
            (
                row
                for row in self.dismissals
                if row["user_id"] == user_id
                and row["plan_id"] == payload["plan_id"]
                and row["transaction_id"] == payload["transaction_id"]
            ),
            None,
        )
        if existing is not None:
            return existing
        row = {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
            **payload,
        }
        self.dismissals.append(row)
        return row


@pytest.fixture(autouse=True)
def _supabase_override() -> Iterator[None]:
    """Never build a real Supabase client while these tests run."""
    app.dependency_overrides[get_supabase_admin] = lambda: object()
    yield
    app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> FakeRepository:
    """Replace the repository's Supabase calls with the in-memory fake."""
    fake = FakeRepository()
    for name in (
        "list_purchase_plans",
        "list_transactions",
        "list_dismissals",
        "insert_dismissal",
    ):
        monkeypatch.setattr(repository, name, getattr(fake, name))
    return fake


def _notifications(client: TestClient, api_prefix: str, user_id: str = USER_ID) -> Any:
    return client.get(f"{api_prefix}/{SECTION}", params={"user_id": user_id})


# --- ping --------------------------------------------------------------------


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json() == {"section": "notifications", "status": "ok"}


def test_notifications_require_a_user_id(client: TestClient, api_prefix: str) -> None:
    assert client.get(f"{api_prefix}/{SECTION}").status_code == 422


# --- matching ----------------------------------------------------------------


def test_empty_when_there_is_nothing_to_match(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = _notifications(client, api_prefix)

    assert response.status_code == 200
    assert response.json() == {"count": 0, "matches": []}


def test_matching_price_and_day_notifies(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction())

    body = _notifications(client, api_prefix).json()

    assert body["count"] == 1
    match = body["matches"][0]
    assert match["id"] == "plan-1:txn-1"
    assert match["plan_id"] == "plan-1"
    assert match["transaction_id"] == "txn-1"
    assert match["card_id"] == CARD_ID
    assert match["product_name"] == "Sony WH-1000XM5"
    assert match["amount"] == 249.99
    assert match["merchant_name"] == "Argos"
    assert match["transaction_date"] == TODAY.isoformat()


def test_a_later_transaction_still_notifies(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction(authorized_date=TODAY + timedelta(days=3)))

    assert _notifications(client, api_prefix).json()["count"] == 1


def test_a_transaction_before_the_plan_does_not_notify(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction(authorized_date=TODAY - timedelta(days=1)))

    assert _notifications(client, api_prefix).json()["count"] == 0


def test_a_transaction_on_another_card_does_not_notify(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction(card_id=OTHER_CARD_ID))

    assert _notifications(client, api_prefix).json()["count"] == 0


@pytest.mark.parametrize("amount", [249.98, 250.0, 240.0])
def test_a_different_price_does_not_notify(
    client: TestClient, api_prefix: str, store: FakeRepository, amount: float
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction(amount=amount))

    assert _notifications(client, api_prefix).json()["count"] == 0


@pytest.mark.parametrize("amount", [-249.99, 0.0])
def test_payments_and_refunds_do_not_notify(
    client: TestClient, api_prefix: str, store: FakeRepository, amount: float
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction(amount=amount))

    assert _notifications(client, api_prefix).json()["count"] == 0


def test_the_posted_date_is_used_when_there_is_no_authorized_date(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    transaction = _transaction(authorized_date=None)
    transaction["posted_date"] = TODAY.isoformat()
    store.transactions.append(transaction)

    assert _notifications(client, api_prefix).json()["count"] == 1


def test_two_matching_transactions_are_listed_newest_first(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    # Planned a week ago, so both purchases are "on or after" the plan date.
    store.plans.append(_plan(created_at=datetime(2026, 11, 1, 9, 0, tzinfo=UTC)))
    store.transactions.append(
        _transaction(transaction_id="old", authorized_date=TODAY - timedelta(days=2))
    )
    store.transactions.append(
        _transaction(transaction_id="new", authorized_date=TODAY, merchant_name="Argos")
    )

    matches = _notifications(client, api_prefix).json()["matches"]

    assert [match["transaction_id"] for match in matches] == ["new", "old"]


def test_another_users_rows_are_ignored(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    other_plan = _plan()
    other_plan["user_id"] = OTHER_USER_ID
    other_transaction = _transaction()
    other_transaction["user_id"] = OTHER_USER_ID
    store.plans.append(other_plan)
    store.transactions.append(other_transaction)

    assert _notifications(client, api_prefix).json()["count"] == 0


def test_a_plan_without_a_product_name_still_matches(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan(product_name=None))
    store.transactions.append(_transaction(merchant_name=None))

    match = _notifications(client, api_prefix).json()["matches"][0]

    assert match["product_name"] is None
    assert match["merchant_name"] == "ARGOS RETAIL LTD"


# --- dismissing (the ✗ action) -----------------------------------------------


def test_dismissing_a_match_hides_it(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction())
    assert _notifications(client, api_prefix).json()["count"] == 1

    dismissed = client.post(
        f"{api_prefix}/{SECTION}/dismissals",
        json={"user_id": USER_ID, "plan_id": "plan-1", "transaction_id": "txn-1"},
    )

    assert dismissed.status_code == 201
    body = dismissed.json()
    assert body["plan_id"] == "plan-1"
    assert body["transaction_id"] == "txn-1"
    assert len(store.dismissals) == 1
    assert _notifications(client, api_prefix).json()["count"] == 0


def test_dismissing_twice_is_idempotent(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    payload = {"user_id": USER_ID, "plan_id": "plan-1", "transaction_id": "txn-1"}

    first = client.post(f"{api_prefix}/{SECTION}/dismissals", json=payload)
    second = client.post(f"{api_prefix}/{SECTION}/dismissals", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert len(store.dismissals) == 1


def test_dismissing_only_silences_that_pair(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.plans.append(_plan())
    store.transactions.append(_transaction(transaction_id="txn-1"))
    store.transactions.append(_transaction(transaction_id="txn-2"))

    client.post(
        f"{api_prefix}/{SECTION}/dismissals",
        json={"user_id": USER_ID, "plan_id": "plan-1", "transaction_id": "txn-1"},
    )

    matches = _notifications(client, api_prefix).json()["matches"]

    assert [match["transaction_id"] for match in matches] == ["txn-2"]


@pytest.mark.parametrize(
    "payload",
    [
        {"plan_id": "plan-1", "transaction_id": "txn-1"},
        {"user_id": USER_ID, "transaction_id": "txn-1"},
        {"user_id": USER_ID, "plan_id": "plan-1"},
    ],
)
def test_dismissal_requires_every_id(
    client: TestClient, api_prefix: str, store: FakeRepository, payload: dict[str, str]
) -> None:
    response = client.post(f"{api_prefix}/{SECTION}/dismissals", json=payload)

    assert response.status_code == 422
    assert store.dismissals == []


# --- service -----------------------------------------------------------------


def test_plans_without_an_amount_are_ignored() -> None:
    plan = _plan(amount=0)
    matches = service.find_matches([plan], [_transaction(amount=0)])

    assert matches == []


def test_dismissed_pairs_are_skipped_by_the_service() -> None:
    matches = service.find_matches(
        [_plan()],
        [_transaction()],
        dismissed={("plan-1", "txn-1")},
    )

    assert matches == []


