"""Tests for the Friends Feed section.

Credential-free: the Supabase dependency is overridden and both sections'
repository modules are replaced with in-memory fakes.
"""

import random
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_supabase_admin
from app.main import app
from app.sections.friends import repository as friends_repository
from app.sections.friends_feed import repository, seed, service

SECTION = "friends-feed"
USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"
SELF = service.SELF_ACTOR


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

    def insert_entry(
        self, client: Any, *, user_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        row = self._row(user_id, payload)
        self.rows.append(row)
        return row

    def insert_entries(
        self, client: Any, *, user_id: str, payloads: list[dict[str, Any]]
    ) -> int:
        for payload in payloads:
            self.rows.append(self._row(user_id, payload))
        return len(payloads)

    def list_entries(
        self, client: Any, *, user_id: str, limit: int
    ) -> list[dict[str, Any]]:
        mine = [row for row in self.rows if row["user_id"] == user_id]
        mine.sort(key=lambda row: row["created_at"], reverse=True)
        return mine[:limit]

    def delete_entries_from_others(
        self, client: Any, *, user_id: str, self_actor: str
    ) -> int:
        removed = [
            row
            for row in self.rows
            if row["user_id"] == user_id and row.get("actor") != self_actor
        ]
        self.rows = [row for row in self.rows if row not in removed]
        return len(removed)


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
        "insert_entry",
        "insert_entries",
        "list_entries",
        "delete_entries_from_others",
    ):
        monkeypatch.setattr(repository, name, getattr(fake, name))
    return fake


def _post_entry(client: TestClient, api_prefix: str, **payload: Any) -> Any:
    return client.post(f"{api_prefix}/{SECTION}/entries", json=payload)


def _feed(client: TestClient, api_prefix: str, **params: Any) -> Any:
    return client.get(
        f"{api_prefix}/{SECTION}/feed", params={"user_id": USER_ID, **params}
    )


# --- ping --------------------------------------------------------------------


def test_ping(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/ping")

    assert response.status_code == 200
    assert response.json() == {"section": "friends-feed", "status": "ok"}


# --- feed --------------------------------------------------------------------


def test_feed_requires_a_user_id(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/{SECTION}/feed")

    assert response.status_code == 422


@pytest.mark.parametrize("limit", [0, 41])
def test_feed_rejects_an_out_of_range_limit(
    client: TestClient, api_prefix: str, store: FakeRepository, limit: int
) -> None:
    response = _feed(client, api_prefix, limit=limit)

    assert response.status_code == 422


def test_feed_is_empty_for_a_new_user(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    """Nothing is invented at request time — the feed is whatever the table holds."""
    response = _feed(client, api_prefix)

    assert response.status_code == 200
    assert response.json()["entries"] == []


def test_feed_is_ordered_newest_first(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    now = datetime.now(UTC)
    for hours_ago, actor in ((5, "James May"), (1, "Priya Shah"), (3, "Tom Ellis")):
        store.rows.append(
            {
                "id": str(uuid4()),
                "user_id": USER_ID,
                "kind": "lesson",
                "actor": actor,
                "action": "completed something",
                "detail": None,
                "created_at": (now - timedelta(hours=hours_ago)).isoformat(),
            }
        )

    entries = _feed(client, api_prefix).json()["entries"]

    assert [entry["actor"] for entry in entries] == ["Priya Shah", "Tom Ellis", "James May"]


def test_is_self_is_derived_from_the_actor(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    store.rows.append(
        {
            "id": str(uuid4()),
            "user_id": USER_ID,
            "kind": "lesson",
            "actor": "James May",
            "action": "completed Financial Arithmetic — Interest and APR",
            "detail": "5/5 correct",
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    _post_entry(client, api_prefix, user_id=USER_ID, kind="recap", score=4, total=5)

    entries = _feed(client, api_prefix).json()["entries"]
    flags = {entry["actor"]: entry["is_self"] for entry in entries}

    assert flags["James May"] is False
    assert flags[SELF] is True


def test_recording_a_lesson_puts_it_at_the_top(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _post_entry(
        client,
        api_prefix,
        user_id=USER_ID,
        kind="lesson",
        lesson_title="Financial Arithmetic — Interest and APR",
        score=4,
        total=5,
    )

    assert created.status_code == 201
    body = created.json()
    assert body["actor"] == "You"
    assert body["kind"] == "lesson"
    assert body["action"] == "completed Financial Arithmetic — Interest and APR"
    assert body["detail"] == "4/5 correct"
    assert body["is_self"] is True
    assert len(store.rows) == 1

    entries = _feed(client, api_prefix).json()["entries"]
    assert entries[0]["id"] == body["id"]
    assert entries[0]["is_self"] is True


def test_recap_entries_use_the_refresh_wording(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    created = _post_entry(
        client, api_prefix, user_id=USER_ID, kind="recap", score=3, total=5
    )

    assert created.status_code == 201
    body = created.json()
    assert body["kind"] == "recap"
    assert body["action"] == "finished a refresh round"
    assert body["detail"] == "3/5 correct"


def test_feed_is_capped_to_the_requested_size(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    for score in (1, 2, 3):
        _post_entry(
            client,
            api_prefix,
            user_id=USER_ID,
            kind="lesson",
            lesson_title=f"Lesson {score}",
            score=score,
            total=5,
        )

    entries = _feed(client, api_prefix, limit=1).json()["entries"]

    assert len(entries) == 1
    assert entries[0]["action"] == "completed Lesson 3"


def test_entries_of_another_user_are_not_included(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    _post_entry(
        client, api_prefix, user_id=OTHER_USER_ID, kind="recap", score=5, total=5
    )

    entries = _feed(client, api_prefix).json()["entries"]

    assert entries == []
    assert len(store.rows) == 1


# --- validation --------------------------------------------------------------


def test_lesson_entries_require_a_title(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = _post_entry(
        client, api_prefix, user_id=USER_ID, kind="lesson", score=1, total=5
    )

    assert response.status_code == 422


def test_score_cannot_exceed_total(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = _post_entry(
        client, api_prefix, user_id=USER_ID, kind="recap", score=9, total=5
    )

    assert response.status_code == 422


def test_entry_requires_a_user_id(
    client: TestClient, api_prefix: str, store: FakeRepository
) -> None:
    response = _post_entry(client, api_prefix, kind="recap", score=1, total=5)

    assert response.status_code == 422


# --- generated friend activity -----------------------------------------------


def _friends(*names: str) -> list[dict[str, Any]]:
    """Friend rows as the friends repository returns them."""
    return [
        {
            "id": str(uuid4()),
            "user_id": USER_ID,
            "friend_name": name,
            "friend_email": f"{name.split()[0].lower()}@example.com",
            "created_at": None,
        }
        for name in names
    ]


def test_seed_writes_activity_for_every_friend(
    client: TestClient, api_prefix: str, store: FakeRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        friends_repository,
        "list_friends",
        lambda client, *, user_id: _friends("James May", "Lucas James", "Priya Shah"),
    )

    written = seed.run(object(), USER_ID)

    assert written >= 3
    assert {row["actor"] for row in store.rows} == {"James May", "Lucas James", "Priya Shah"}
    assert all(row["user_id"] == USER_ID for row in store.rows)
    assert all(row["detail"] is not None or row["kind"] == "streak" for row in store.rows)

    entries = _feed(client, api_prefix).json()["entries"]
    assert len(entries) == written
    assert all(entry["is_self"] is False for entry in entries)


def test_seed_replaces_old_friend_activity_but_keeps_your_own(
    client: TestClient, api_prefix: str, store: FakeRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    _post_entry(client, api_prefix, user_id=USER_ID, kind="recap", score=4, total=5)
    store.rows.append(
        {
            "id": str(uuid4()),
            "user_id": USER_ID,
            "kind": "lesson",
            "actor": "Old Friend",
            "action": "completed something",
            "detail": None,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    monkeypatch.setattr(
        friends_repository, "list_friends", lambda client, *, user_id: _friends("James May")
    )

    seed.run(object(), USER_ID)

    actors = {row["actor"] for row in store.rows}
    assert "Old Friend" not in actors
    assert SELF in actors
    assert "James May" in actors


def test_seed_does_nothing_when_the_user_has_no_friends(
    store: FakeRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        friends_repository, "list_friends", lambda client, *, user_id: []
    )

    assert seed.run(object(), USER_ID) == 0
    assert store.rows == []


def test_generated_activity_looks_like_real_activity() -> None:
    now = datetime.now(UTC)
    rows = seed.build_activity(
        ["James May", "Lucas James"], now=now, rng=random.Random(7)
    )

    assert len(rows) >= 2
    for row in rows:
        assert row["kind"] in {"lesson", "recap", "streak"}
        assert row["action"]
        stamp = datetime.fromisoformat(row["created_at"])
        assert stamp < now
        assert (now - stamp).total_seconds() <= seed.SPREAD_MINUTES * 60
    lessons = {row["action"] for row in rows if row["kind"] == "lesson"}
    assert lessons <= {f"completed {title}" for title, _ in seed.lesson_titles()}


def test_build_activity_is_deterministic_for_the_same_seed() -> None:
    now = datetime.now(UTC)
    first = seed.build_activity(["James May"], now=now, rng=random.Random(3))
    second = seed.build_activity(["James May"], now=now, rng=random.Random(3))

    assert [row["action"] for row in first] == [row["action"] for row in second]
    assert [row["created_at"] for row in first] == [row["created_at"] for row in second]


