#!/usr/bin/env python3
"""End-to-end manual test for the Friends Feed section.

Runs the two user-facing steps against a locally running API:
  1. POST /entries — record a finished lesson (what the lesson runner sends).
  2. GET  /feed    — print the merged feed, newest first.

Usage (from backend/):
    ../.venv/bin/python scripts/try_friends_feed.py [user-id]

Without a user id it resolves the demo account (`demo@demo.com`) through the
Supabase admin API, using SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from
backend/.env.

Requirements:
  - The API running on http://127.0.0.1:8000 (uvicorn app.main:app --port 8000)
    started from backend/ so it reads backend/.env.
  - `app/sections/friends_feed/schema.sql` applied in the Supabase SQL editor.
  - `httpx` (already in the venv).

This script only needs `httpx`, not the app package, so it can run standalone.
"""

import os
import sys
from pathlib import Path

import httpx

API = os.environ.get("CREDITMATE_API", "http://127.0.0.1:8000")
BASE_URL = f"{API}/api/v1/friends-feed"
FRIENDS_URL = f"{API}/api/v1/friends"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
DEMO_EMAIL = "demo@demo.com"
#: Throwaway friend used to prove add/list/remove; deleted again before exiting.
TEST_FRIEND_EMAIL = "qa.friend@example.com"


def read_env() -> dict[str, str]:
    """Minimal .env reader — this script must not import the app package."""
    values: dict[str, str] = {}
    if not ENV_FILE.is_file():
        return values
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def demo_user_id(env: dict[str, str]) -> str:
    """Look the demo account up in Supabase Auth (service role, backend only)."""
    url = env.get("SUPABASE_URL", "").rstrip("/")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        sys.exit(
            "Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in backend/.env "
            "— or pass a user id: python scripts/try_friends_feed.py <uuid>"
        )

    response = httpx.get(
        f"{url}/auth/v1/admin/users",
        params={"page": 1, "per_page": 200},
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=30,
    )
    response.raise_for_status()
    for user in response.json().get("users", []):
        if user.get("email") == DEMO_EMAIL:
            return str(user["id"])
    sys.exit(f"No {DEMO_EMAIL} user found — run scripts/seed_demo.py first.")


def print_entries(entries: list[dict[str, object]]) -> None:
    for entry in entries:
        detail = f" ({entry['detail']})" if entry.get("detail") else ""
        mine = "you " if entry.get("is_self") else "    "
        stamp = str(entry["occurred_at"])[11:16]
        print(f"  {stamp}  {mine}{entry['actor']:14} {entry['action']}{detail}")


def check_friends(client: httpx.Client, user_id: str) -> None:
    """Add a throwaway friend, list the friends, then remove it again."""
    created = client.post(
        FRIENDS_URL, json={"user_id": user_id, "email": TEST_FRIEND_EMAIL.upper()}
    )
    if created.status_code == 409:
        print(f"friend {TEST_FRIEND_EMAIL} already saved (409 on re-run)")
    elif created.status_code != 201:
        sys.exit(f"POST /friends failed ({created.status_code}): {created.text}")
    else:
        friend = created.json()
        print(f"added friend: {friend['friend_name']} <{friend['friend_email']}>")
        if friend["friend_email"] != TEST_FRIEND_EMAIL:
            sys.exit("FAILED: the API should store the address lower-cased")

    listed = client.get(FRIENDS_URL, params={"user_id": user_id})
    if listed.status_code != 200:
        sys.exit(f"GET /friends failed ({listed.status_code}): {listed.text}")
    friends = listed.json()
    print(f"\n{len(friends)} friend(s) on the list:")
    for friend in friends:
        print(f"  {friend['friend_name']:16} <{friend['friend_email']}>")

    duplicate = client.post(
        FRIENDS_URL, json={"user_id": user_id, "email": TEST_FRIEND_EMAIL}
    )
    if duplicate.status_code != 409:
        sys.exit(f"FAILED: adding the same friend twice returned {duplicate.status_code}")

    target = next(
        (friend for friend in friends if friend["friend_email"] == TEST_FRIEND_EMAIL), None
    )
    if target is None:
        sys.exit("FAILED: the friend just added is not in the list")
    removed = client.delete(f"{FRIENDS_URL}/{target['id']}", params={"user_id": user_id})
    if removed.status_code != 204:
        sys.exit(f"DELETE /friends failed ({removed.status_code}): {removed.text}")
    print("removed the test friend again (204)")


def main() -> int:
    env = read_env()
    user_id = sys.argv[1] if len(sys.argv) > 1 else demo_user_id(env)

    with httpx.Client(timeout=30) as client:
        health = client.get(f"{API}/health")
        if health.status_code != 200:
            sys.exit(
                f"The API is not answering on {API} — start it from backend/:\n"
                "    ../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000"
            )

        created = client.post(
            f"{BASE_URL}/entries",
            json={
                "user_id": user_id,
                "kind": "lesson",
                "lesson_title": "Financial Arithmetic — Interest and APR",
                "score": 4,
                "total": 5,
            },
        )
        if created.status_code != 201:
            sys.exit(f"POST /entries failed ({created.status_code}): {created.text}")
        print(f"recorded: {created.json()['action']} ({created.json()['detail']})")

        feed = client.get(f"{BASE_URL}/feed", params={"user_id": user_id, "limit": 12})
        if feed.status_code != 200:
            sys.exit(f"GET /feed failed ({feed.status_code}): {feed.text}")

        entries = feed.json()["entries"]
        print(f"\n{len(entries)} entries, newest first:")
        print_entries(entries)

        if not entries:
            sys.exit("FAILED: expected at least the hardcoded friend activity")
        if not entries[0]["is_self"]:
            sys.exit("FAILED: the entry just recorded should be at the top")
        print("feed OK — the new entry is at the top.\n")

        check_friends(client, user_id)

    print("\nOK — feed and friends both behave.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
