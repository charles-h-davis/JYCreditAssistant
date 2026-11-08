"""End-to-end smoke test of the demo account against the running API.

Exercises every endpoint the frontend uses (including the write paths) and prints
a pass/fail line per call. Run from `backend/` with uvicorn on :8000:

    ..\\.venv\\Scripts\\python.exe scripts\\verify_demo.py
"""

import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import random  # noqa: E402
from datetime import date  # noqa: E402

import seed_demo  # noqa: E402  (same folder, imported for the balance identity)

BASE = "http://127.0.0.1:8000/api/v1"
DEMO_EMAIL = "demo@demo.com"
RESULTS: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((ok, name))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{f' — {detail}' if detail else ''}")


def main() -> int:
    client = httpx.Client(timeout=90)
    health = client.get("http://127.0.0.1:8000/health")
    check("health", health.status_code == 200, str(health.status_code))

    # Find the demo user id via the service-role client (same as the seed does).
    from app.core.database import get_supabase_admin

    users = get_supabase_admin().auth.admin.list_users()
    demo = next((u for u in users if (u.email or "").lower() == DEMO_EMAIL), None)
    if demo is None:
        print("Demo user missing — run scripts/seed_demo.py first.")
        return 1
    uid = str(demo.id)

    for section in ("card-storage", "cost-to-buy", "credit-learning", "ai-assistant"):
        response = client.get(f"{BASE}/{section}/ping")
        check(f"{section}/ping", response.status_code == 200, response.text[:60])

    cards = client.get(f"{BASE}/card-storage/cards", params={"user_id": uid})
    check("list cards", cards.status_code == 200, f"{len(cards.json())} cards")
    card = cards.json()[0]
    card_id = card["id"]
    check(
        "card has APR + balance",
        card["purchase_apr"] is not None and card["current_balance"] > 0,
        f"£{card['current_balance']} @ {card['purchase_apr']}%",
    )

    transactions = client.get(
        f"{BASE}/card-storage/cards/{card_id}/transactions", params={"user_id": uid}
    )
    rows = transactions.json()
    months = sorted({row["authorized_date"][:7] for row in rows if row["authorized_date"]})
    check(
        "list transactions",
        transactions.status_code == 200 and len(rows) > 20,
        f"{len(rows)} rows across {months}",
    )

    # Every card's stored balance must equal its opening balance plus the sum of
    # the transactions the UI can actually show.
    history = seed_demo.build_history(date.today(), random.Random(20260711))
    reconciled = True
    detail = []
    for index, plan in enumerate(history):
        card_rows = client.get(
            f"{BASE}/card-storage/cards/{cards.json()[index]['id']}/transactions",
            params={"user_id": uid},
        ).json()
        net = round(sum(row["amount"] for row in card_rows), 2)
        expected = round(plan["opening_balance"] + net, 2)
        stored = round(cards.json()[index]["current_balance"], 2)
        detail.append(f"{plan['nickname']} {expected:.2f}")
        if abs(expected - stored) > 0.01:
            reconciled = False
            detail[-1] += f" != {stored:.2f}"
    check(
        "balance reconciles with transaction history",
        reconciled,
        ", ".join(detail),
    )

    payment = client.get(
        f"{BASE}/cost-to-buy/monthly-payment", params={"user_id": uid, "card_id": card_id}
    )
    check(
        "get monthly payment",
        payment.status_code == 200 and payment.json()["monthly_payment"] > 0,
        str(payment.json().get("monthly_payment")),
    )

    # Write back the same value so the check is idempotent and leaves the demo
    # account exactly as seeded.
    stored_payment = float(payment.json()["monthly_payment"])
    put = client.put(
        f"{BASE}/cost-to-buy/monthly-payment",
        json={"user_id": uid, "card_id": card_id, "monthly_payment": stored_payment},
    )
    check(
        "put monthly payment",
        put.status_code == 200 and put.json()["monthly_payment"] == stored_payment,
    )

    plans = client.get(f"{BASE}/cost-to-buy/purchase-plans", params={"user_id": uid})
    check("list purchase plans", plans.status_code == 200, f"{len(plans.json())} plans")

    created = client.post(
        f"{BASE}/cost-to-buy/purchase-plans",
        json={
            "user_id": uid,
            "card_id": card_id,
            "product_name": "Smoke test kettle",
            "purchase_amount": 39.99,
            # Confirming a plan sets the card's repayment, so keep the value the
            # seed wrote and the demo account stays pristine.
            "monthly_payment": stored_payment,
        },
    )
    check("create purchase plan", created.status_code == 201, created.text[:80])
    plan_id = created.json().get("id") if created.status_code == 201 else None

    if plan_id:
        deleted = client.delete(
            f"{BASE}/cost-to-buy/purchase-plans/{plan_id}", params={"user_id": uid}
        )
        check("delete purchase plan", deleted.status_code == 204, str(deleted.status_code))
        again = client.delete(
            f"{BASE}/cost-to-buy/purchase-plans/{plan_id}", params={"user_id": uid}
        )
        check("delete again -> 404", again.status_code == 404, str(again.status_code))

    # VERIFY_TAIL
    estimate = client.post(
        f"{BASE}/cost-to-buy/estimate",
        json={"purchase_amount": 120.0, "purchase_apr": 34.9, "monthly_payment": 150.0},
    )
    check("estimate", estimate.status_code == 200, f"£{estimate.json().get('total_paid')}")

    full = client.post(
        f"{BASE}/cost-to-buy/estimate",
        json={"purchase_amount": 500.0, "purchase_apr": 34.9, "monthly_payment": 500.0},
    )
    body = full.json() if full.status_code == 200 else {}
    check(
        "paying in full settles in 1 month with no interest",
        body.get("months_to_payoff") == 1 and body.get("total_interest") == 0,
        f"{body.get('months_to_payoff')} months, £{body.get('total_interest')} interest",
    )

    impact = client.post(
        f"{BASE}/cost-to-buy/purchase-impact",
        json={
            "current_balance": card["current_balance"],
            "purchase_apr": card["purchase_apr"],
            "purchase_amount": 123.45,
            "current_monthly_payment": 150.0,
            "closing_day": card["closing_day"] or 1,
            "statement_day": card["statement_day"] or 1,
        },
    )
    extra = impact.json().get("extra_total_paid") if impact.status_code == 200 else None
    check("purchase impact", impact.status_code == 200, f"extra paid £{extra}")

    roadmap = client.get(f"{BASE}/credit-learning/roadmap", params={"user_id": uid})
    body = roadmap.json() if roadmap.status_code == 200 else {}
    categories = body.get("categories", [])
    done = sum(1 for c in categories for lesson in c["lessons"] if lesson["completed"])
    check(
        "roadmap",
        roadmap.status_code == 200 and len(categories) == 5,
        f"{len(categories)} activities, {done} lessons done, streak "
        f"{body.get('streak', {}).get('current_streak')}",
    )

    slug = categories[0]["lessons"][0]["slug"] if categories else None
    lesson = client.get(f"{BASE}/credit-learning/lessons/{slug}")
    questions = lesson.json().get("questions", [])
    check("lesson detail", lesson.status_code == 200 and len(questions) == 5, slug)

    verdict = client.post(
        f"{BASE}/credit-learning/questions/{questions[0]['id']}/answer",
        json={"selected_index": 0},
    )
    check(
        "instant answer check",
        verdict.status_code == 200
        and verdict.json().get("correct_index") in (0, 1, 2, 3),
        f"correct={verdict.json().get('correct')}",
    )

    attempt = client.post(
        f"{BASE}/credit-learning/lessons/{slug}/attempt",
        json={
            "user_id": uid,
            "answers": [{"question_id": q["id"], "selected_index": 0} for q in questions],
        },
    )
    check(
        "lesson attempt",
        attempt.status_code == 200,
        f"score {attempt.json().get('score')}/{attempt.json().get('total')}",
    )

    recap = client.get(f"{BASE}/credit-learning/recap", params={"user_id": uid})
    check("recap", recap.status_code == 200, f"{len(recap.json().get('questions', []))} questions")

    image = Path(__file__).resolve().parents[2] / "frontend" / "design refs" / "iPhone 17 - 12.jpg"
    if image.exists():
        with image.open("rb") as handle:
            extract = client.post(
                f"{BASE}/cost-to-buy/extract",
                files={"file": (image.name, handle, "image/jpeg")},
            )
        payload = extract.json() if extract.status_code == 200 else {}
        check(
            "gemini extract",
            extract.status_code == 200,
            f"{payload.get('product_name')!r} @ {payload.get('price')}",
        )

    started = time.perf_counter()
    payload: dict = {}
    for _attempt in range(3):
        chat = client.post(
            f"{BASE}/ai-assistant/chat",
            json={"message": "Should I pay off my highest APR card first?"},
        )
        payload = chat.json() if chat.status_code == 200 else {}
        if chat.status_code == 200:
            break
        print(f"  (assistant returned {chat.status_code}, retrying in 5s)")
        time.sleep(5)
    elapsed = time.perf_counter() - started
    check(
        "assistant chat",
        chat.status_code == 200 and payload.get("in_scope") is True,
        f"{elapsed:.1f}s — {str(payload.get('reply'))[:70]}...",
    )

    failed = [name for ok, name in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        print("Failed:", ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
