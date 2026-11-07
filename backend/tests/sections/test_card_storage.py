"""Tests for the Card Storage section.

The suite must pass without Supabase or Plaid credentials: both dependencies are
overridden with in-memory fakes, and the Plaid -> row mapping functions are
exercised directly (they are pure).
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_supabase_admin
from app.main import app
from app.sections.card_storage import repository, service
from app.sections.card_storage.plaid_client import get_plaid_client

SECTION = "card-storage"
USER_ID = "11111111-1111-1111-1111-111111111111"

VALID_CARD = {
    "nickname": "Everyday card",
    "issuer": "Chase",
    "last_four": "4321",
    "credit_limit": 5000.0,
    "current_balance": 1875.4,
    "purchase_apr": 24.99,
    "closing_day": 12,
    "statement_day": 5,
}

CARD_ROW = {
    "id": "card-1",
    "user_id": USER_ID,
    "plaid_item_id": None,
    "plaid_account_id": None,
    "is_secured": False,
    "created_at": "2026-07-01T00:00:00+00:00",
    "updated_at": "2026-07-01T00:00:00+00:00",
    **VALID_CARD,
}

ACCOUNTS_RESPONSE = {
    "accounts": [
        {
            "account_id": "acc-credit-1",
            "name": "Plaid Credit Card",
            "mask": "3333",
            "type": "credit",
            "subtype": "credit card",
            "balances": {"available": None, "current": 410.0, "limit": 2000.0},
        },
        {
            "account_id": "acc-checking-1",
            "name": "Plaid Checking",
            "mask": "0000",
            "type": "depository",
            "subtype": "checking",
            "balances": {"available": 100.0, "current": 110.0, "limit": None},
        },
    ],
    "item": {
        "item_id": "item-1",
        "institution_id": "ins_56",
        "institution_name": "Chase",
    },
}

LIABILITIES_RESPONSE = {
    "liabilities": {
        "credit": [
            {
                "account_id": "acc-credit-1",
                "aprs": [
                    {"apr_type": "cash_apr", "apr_percentage": 27.95},
                    {"apr_type": "purchase_apr", "apr_percentage": 12.5},
                ],
                "last_statement_issue_date": "2026-06-15",
                "next_payment_due_date": "2026-07-09",
            }
        ]
    }
}

TRANSACTIONS = [
    {
        "account_id": "acc-credit-1",
        "transaction_id": "txn-1",
        "name": "Blue Bottle Coffee",
        "merchant_name": "Blue Bottle",
        "amount": 6.5,
        "date": "2026-07-01",
        "authorized_date": "2026-06-30",
        "pending": False,
        "personal_finance_category": {"primary": "FOOD_AND_DRINK"},
        "iso_currency_code": "USD",
    },
    {
        "account_id": "acc-credit-1",
        "transaction_id": "txn-2",
        "name": "Payment Thank You",
        "merchant_name": None,
        "amount": -100.0,
        "date": "2026-06-28",
        "category": ["Payment", "Credit Card"],
        "pending": False,
        "iso_currency_code": "USD",
    },
    {
        "account_id": "acc-checking-1",
        "transaction_id": "txn-3",
        "name": "Not a card transaction",
        "amount": 12.0,
        "date": "2026-06-27",
        "pending": False,
    },
]


class FakePlaidClient:
    """Stand-in for `PlaidClient` returning sandbox-shaped payloads."""

    def __init__(self) -> None:
        self.accounts_response = ACCOUNTS_RESPONSE
        self.liabilities_response = LIABILITIES_RESPONSE
        self.added = TRANSACTIONS

    def sandbox_public_token_create(
        self, institution_id: str, products: list[str] | None = None
    ) -> str:
        return f"public-sandbox-{institution_id}"

    def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        return {"access_token": "access-sandbox-123", "item_id": "item-1"}

    def accounts_get(self, access_token: str) -> dict[str, Any]:
        assert access_token == "access-sandbox-123"
        return self.accounts_response

    def liabilities_get(self, access_token: str) -> dict[str, Any]:
        return self.liabilities_response

    def sync_all_transactions(
        self, access_token: str, *, cursor: str | None = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
        return self.added, [], [], "cursor-2"


@pytest.fixture(autouse=True)
def offline_dependencies() -> Iterator[None]:
    """Keep the endpoint tests offline: fake DB client and fake Plaid client."""
    app.dependency_overrides[get_supabase_admin] = lambda: object()
    app.dependency_overrides[get_plaid_client] = lambda: FakePlaidClient()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> "FakeRepository":
    """Replace every repository call with an in-memory store."""
    fake = FakeRepository()
    for name in (
        "list_cards",
        "get_card",
        "insert_card",
        "upsert_cards",
        "list_transactions",
        "upsert_transactions",
        "delete_transactions_by_plaid_ids",
        "get_plaid_item",
        "upsert_plaid_item",
        "update_plaid_item_cursor",
    ):
        monkeypatch.setattr(repository, name, getattr(fake, name))
    return fake


class FakeRepository:
    """In-memory stand-in for the repository module."""

    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}
        self.cards: dict[str, dict[str, Any]] = {}
        self.transactions: dict[str, dict[str, Any]] = {}

    # cards
    def list_cards(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        return list(self.cards.values())

    def get_card(self, client: Any, *, user_id: str, card_id: str) -> dict[str, Any] | None:
        return self.cards.get(card_id)

    def insert_card(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        row = {**CARD_ROW, **payload, "user_id": user_id}
        self.cards[row["id"]] = row
        return row

    def upsert_cards(
        self, client: Any, *, user_id: str, payloads: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for payload in payloads:
            row = {
                "id": f"card-{payload['plaid_account_id']}",
                "user_id": user_id,
                "is_secured": False,
                **payload,
            }
            self.cards[row["id"]] = row
            rows.append(row)
        return rows

    # plaid items
    def get_plaid_item(
        self, client: Any, *, user_id: str, item_id: str
    ) -> dict[str, Any] | None:
        return self.items.get(item_id)

    def upsert_plaid_item(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        row = {"id": "item-row-1", "user_id": user_id, **payload}
        self.items[payload["item_id"]] = row
        return row

    def update_plaid_item_cursor(
        self, client: Any, *, user_id: str, item_id: str, cursor: str | None
    ) -> None:
        if cursor:
            self.items.setdefault(item_id, {"id": "item-row-1", "user_id": user_id})
            self.items[item_id]["transactions_cursor"] = cursor

    # transactions
    def list_transactions(
        self, client: Any, *, user_id: str, card_id: str
    ) -> list[dict[str, Any]]:
        return [row for row in self.transactions.values() if row["card_id"] == card_id]

    def upsert_transactions(
        self,
        client: Any,
        *,
        user_id: str,
        card_id: str,
        payloads: list[dict[str, Any]],
    ) -> int:
        for payload in payloads:
            transaction_id = payload["plaid_transaction_id"]
            self.transactions[transaction_id] = {
                "id": f"txn-row-{transaction_id}",
                "user_id": user_id,
                "card_id": card_id,
                **payload,
            }
        return len(payloads)

    def delete_transactions_by_plaid_ids(
        self, client: Any, *, user_id: str, plaid_transaction_ids: list[str]
    ) -> int:
        removed = 0
        for transaction_id in plaid_transaction_ids:
            if self.transactions.pop(transaction_id, None) is not None:
                removed += 1
        return removed


# --- endpoints -------------------------------------------------------------


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json()["section"] == SECTION


def test_create_card_rejects_full_pan(client: TestClient, api_prefix: str) -> None:
    """`last_four` must be exactly four digits — no full card numbers."""
    payload = {**VALID_CARD, "last_four": "4321123456789012"}

    response = client.post(
        f"{api_prefix}/{SECTION}/cards?user_id={USER_ID}", json=payload
    )

    assert response.status_code == 422


def test_create_card_rejects_invalid_day(client: TestClient, api_prefix: str) -> None:
    payload = {**VALID_CARD, "statement_day": 32}

    response = client.post(
        f"{api_prefix}/{SECTION}/cards?user_id={USER_ID}", json=payload
    )

    assert response.status_code == 422


def test_create_card_rejects_apr_above_100(client: TestClient, api_prefix: str) -> None:
    payload = {**VALID_CARD, "purchase_apr": 150}

    response = client.post(
        f"{api_prefix}/{SECTION}/cards?user_id={USER_ID}", json=payload
    )

    assert response.status_code == 422


def test_create_card_persists(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.post(
        f"{api_prefix}/{SECTION}/cards?user_id={USER_ID}", json=VALID_CARD
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "card-1"
    assert body["user_id"] == USER_ID
    assert body["closing_day"] == 12
    assert body["statement_day"] == 5
    assert body["purchase_apr"] == 24.99
    assert "card-1" in store.cards


def test_create_card_rejects_balance_above_limit(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    payload = {**VALID_CARD, "current_balance": 6000.0}

    response = client.post(
        f"{api_prefix}/{SECTION}/cards?user_id={USER_ID}", json=payload
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_list_cards(client: TestClient, api_prefix: str, store: FakeRepository) -> None:
    store.cards["card-1"] = CARD_ROW

    response = client.get(f"{api_prefix}/{SECTION}/cards?user_id={USER_ID}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "card-1"
    assert body[0]["purchase_apr"] == 24.99


def test_list_transactions_returns_404_for_unknown_card(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = client.get(
        f"{api_prefix}/{SECTION}/cards/missing/transactions?user_id={USER_ID}"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_list_transactions_returns_history(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.cards["card-1"] = CARD_ROW
    store.transactions["txn-1"] = {
        "id": "txn-row-1",
        "user_id": USER_ID,
        "card_id": "card-1",
        **service.build_transaction_payload(TRANSACTIONS[0]),
    }

    response = client.get(
        f"{api_prefix}/{SECTION}/cards/card-1/transactions?user_id={USER_ID}"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["plaid_transaction_id"] == "txn-1"
    assert body[0]["amount"] == 6.5
    assert body[0]["posted_date"] == "2026-07-01"


# --- pure Plaid -> row mapping ---------------------------------------------


def test_build_card_payload_maps_plaid_fields() -> None:
    account = ACCOUNTS_RESPONSE["accounts"][0]
    liability = LIABILITIES_RESPONSE["liabilities"]["credit"][0]

    payload = service.build_card_payload(account, liability, issuer="Chase")

    assert payload == {
        "plaid_account_id": "acc-credit-1",
        "nickname": "Plaid Credit Card",
        "issuer": "Chase",
        "last_four": "3333",
        "credit_limit": 2000.0,
        "current_balance": 410.0,
        "available_balance": None,
        "purchase_apr": 12.5,
        "closing_day": 15,
        "statement_day": 9,
    }


def test_build_transaction_payload_maps_plaid_fields() -> None:
    payload = service.build_transaction_payload(TRANSACTIONS[0])

    assert payload["category"] == "FOOD_AND_DRINK"
    assert payload["amount"] == 6.5
    assert payload["posted_date"] == "2026-07-01"
    assert payload["pending"] is False
    assert payload["iso_currency_code"] == "USD"

    legacy = service.build_transaction_payload(TRANSACTIONS[1])

    assert legacy["category"] == "Payment"
    assert legacy["amount"] == -100.0


# --- Plaid sync ------------------------------------------------------------


def test_sync_loads_cards_and_transactions_idempotently(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    url = f"{api_prefix}/{SECTION}/plaid/sync"
    payload = {"user_id": USER_ID}

    first = client.post(url, json=payload)

    assert first.status_code == 200
    body = first.json()
    assert body["item_id"] == "item-1"
    assert body["institution_name"] == "Chase"
    assert body["cards_synced"] == 1
    assert body["transactions_added"] == 2
    assert body["transactions_removed"] == 0
    assert body["next_cursor"] == "cursor-2"

    # Only credit accounts become cards; the checking-account transaction is skipped.
    assert list(store.cards) == ["card-acc-credit-1"]
    assert set(store.transactions) == {"txn-1", "txn-2"}
    assert store.items["item-1"]["transactions_cursor"] == "cursor-2"

    synced_card = store.cards["card-acc-credit-1"]
    assert synced_card["closing_day"] == 15
    assert synced_card["statement_day"] == 9
    assert synced_card["purchase_apr"] == 12.5
    assert synced_card["credit_limit"] == 2000.0
    assert synced_card["current_balance"] == 410.0
    assert synced_card["available_balance"] is None
    assert synced_card["plaid_item_id"] == "item-row-1"

    # A second sync must not duplicate rows.
    second = client.post(url, json=payload)

    assert second.status_code == 200
    assert set(store.transactions) == {"txn-1", "txn-2"}
    assert len(store.cards) == 1


def test_sync_returns_503_without_plaid_credentials(
    client: TestClient,
    api_prefix: str,
    store: FakeRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.dependency_overrides.pop(get_plaid_client, None)
    monkeypatch.setattr(settings, "plaid_client_id", "")
    monkeypatch.setattr(settings, "plaid_secret", "")

    response = client.post(
        f"{api_prefix}/{SECTION}/plaid/sync", json={"user_id": USER_ID}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "plaid_not_configured"
