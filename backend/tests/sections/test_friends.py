"""Tests for the Friends section.

Credential-free: the Supabase dependency is overridden and the repository module
is replaced with an in-memory fake.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_supabase_admin
from app.main import app
from app.sections.friends import repository, seed, service
from app.sections.friends.content import DEFAULT_FRIENDS

SECTION = "friends"
USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"


class FakeRepository:
    """In-memory stand-in for `repository`."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def _row(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
            **payload,
        }

    def list_friends(self, client: Any, *, user_id: str) -> list[dict[str, Any]]:
        mine = [row for row in self.rows if row["user_id"] == user_id]
        mine.sort(key=lambda row: row["created_at"], reverse=True)
        return mine

    def get_friend(
        self, client: Any, *, user_id: str, email: str
    ) -> dict[str, Any] | None:
        return next(
            (
                row
                for row in self.rows
                if row["user_id"] == user_id and row["friend_email"] == email
            ),
            None,
        )

    def insert_friend(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        row = self._row(user_id, payload)
        self.rows.append(row)
        return row

    def upsert_friend(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        existing = self.get_friend(
            client, user_id=user_id, email=payload["friend_email"]
        )
        if existing is not None:
            existing.update(payload)
            return existing
        return self.insert_friend(client, user_id=user_id, payload=payload)

    def delete_friend(
        self, client: Any, *, user_id: str, friend_id: str
    ) -> list[dict[str, Any]]:
        removed = [
            row
            for row in self.rows
            if row["user_id"] == user_id and row["id"] == friend_id
        ]
        self.rows = [row for row in self.rows if row not in removed]
        return removed


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
        "list_friends",
        "get_friend",
        "insert_friend",
        "upsert_friend",
        "delete_friend",
    ):
        monkeypatch.setattr(repository, name, getattr(fake, name))
    return fake


def _add(client: TestClient, api_prefix: str, **payload: Any) -> Any:
    return client.post(f"{api_prefix}/{SECTION}", json=payload)


def _list(client: TestClient, api_prefix: str, user_id: str = USER_ID) -> Any:
    return client.get(f"{api_prefix}/{SECTION}", params={"user_id": user_id})


# --- ping --------------------------------------------------------------------


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json() == {"section": "friends", "status": "ok"}


# --- adding ------------------------------------------------------------------


def test_add_friend_derives_a_name_from_the_email(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _add(client, api_prefix, user_id=USER_ID, email="lucas.james@example.com")

    assert created.status_code == 201
    body = created.json()
    assert body["friend_name"] == "Lucas James"
    assert body["friend_email"] == "lucas.james@example.com"
    assert body["user_id"] == USER_ID
    assert len(store.rows) == 1


def test_add_friend_uses_the_supplied_name(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _add(
        client, api_prefix, user_id=USER_ID, email="l.j@example.com", name="  Lucas J  "
    )

    assert created.status_code == 201
    assert created.json()["friend_name"] == "Lucas J"


def test_add_friend_normalises_the_email(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _add(client, api_prefix, user_id=USER_ID, email="  Priya.Shah@Example.COM ")

    assert created.status_code == 201
    assert created.json()["friend_email"] == "priya.shah@example.com"


def test_adding_the_same_friend_twice_is_a_conflict(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _add(client, api_prefix, user_id=USER_ID, email="tom.ellis@example.com")

    duplicate = _add(client, api_prefix, user_id=USER_ID, email="TOM.ELLIS@example.com")

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "conflict"
    assert len(store.rows) == 1


@pytest.mark.parametrize(
    "email", ["not-an-email", "no@domain", "@example.com", "two words@example.com"]
)
def test_add_friend_rejects_a_non_email(
    client: TestClient, api_prefix: str, store: FakeRepository, email: str
) -> None:
    response = _add(client, api_prefix, user_id=USER_ID, email=email)

    assert response.status_code == 422
    assert store.rows == []


def test_add_friend_requires_a_user_id(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = _add(client, api_prefix, email="aisha.khan@example.com")

    assert response.status_code == 422


# --- listing -----------------------------------------------------------------


def test_list_requires_a_user_id(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}")

    assert response.status_code == 422


def test_list_returns_only_the_users_own_friends(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _add(client, api_prefix, user_id=USER_ID, email="marco.rossi@example.com")
    _add(client, api_prefix, user_id=OTHER_USER_ID, email="someone.else@example.com")

    mine = _list(client, api_prefix).json()

    assert len(mine) == 1
    assert mine[0]["friend_email"] == "marco.rossi@example.com"


def test_list_is_empty_for_a_new_user(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = _list(client, api_prefix)

    assert response.status_code == 200
    assert response.json() == []


# --- removing ----------------------------------------------------------------


def test_remove_friend_deletes_the_row(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _add(client, api_prefix, user_id=USER_ID, email="sofia.bianchi@example.com")

    removed = client.delete(
        f"{api_prefix}/{SECTION}/{created.json()['id']}", params={"user_id": USER_ID}
    )

    assert removed.status_code == 204
    assert _list(client, api_prefix).json() == []


def test_removing_somebody_elses_friend_is_a_404(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _add(client, api_prefix, user_id=USER_ID, email="daniel.okafor@example.com")

    response = client.delete(
        f"{api_prefix}/{SECTION}/{created.json()['id']}",
        params={"user_id": OTHER_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


# --- service + seed ----------------------------------------------------------


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("james.may@example.com", "James May"),
        ("lucas_james@example.com", "Lucas James"),
        ("priya-shah+credit@example.com", "Priya Shah"),
        ("AISHA@example.com", "Aisha"),
        ("single@example.com", "Single"),
    ],
)
def test_display_name_from_email(email: str, expected: str) -> None:
    assert service.display_name_from_email(email) == expected


def test_normalize_email_trims_and_lowercases() -> None:
    assert service.normalize_email("  Tom.Ellis@Example.com ") == "tom.ellis@example.com"


def test_seed_writes_every_demo_friend(store: FakeRepository) -> None:
    written = seed.run(object(), USER_ID)

    assert written == len(DEFAULT_FRIENDS)
    assert len(store.rows) == len(DEFAULT_FRIENDS)
    assert {row["friend_email"] for row in store.rows} == {
        friend.email for friend in DEFAULT_FRIENDS
    }


def test_seed_is_idempotent(store: FakeRepository) -> None:
    seed.run(object(), USER_ID)
    seed.run(object(), USER_ID)

    assert len(store.rows) == len(DEFAULT_FRIENDS)

