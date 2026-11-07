#!/usr/bin/env python3
"""End-to-end manual test for the Cost to Buy section.

Runs the two user-facing steps against a locally running API:
  1. POST /extract         — read a product name + price from an image (Gemini).
  2. POST /purchase-impact — extra cost of that purchase on your card.

Usage (from backend/):
    ../.venv/bin/python scripts/try_cost_to_buy.py /path/to/image.jpg

Requirements:
  - The API running on http://127.0.0.1:8000 (uvicorn app.main:app --port 8000)
    started from backend/ so it reads backend/.env, with GEMINI_API_KEY set.
  - `httpx` (already in the venv).

This script only needs `httpx`, not the app package, so it can run standalone.
"""

import mimetypes
import os
import sys

import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1/cost-to-buy"

# Your card. closing_day / statement_day only shift the payoff DATE, not the
# money totals, so these defaults are fine for testing.
CARD = {
    "current_balance": 2000.0,
    "purchase_apr": 24.99,
    "current_monthly_payment": 150.0,
    "closing_day": 12,
    "statement_day": 5,
}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/try_cost_to_buy.py /path/to/image.jpg")

    image_path = sys.argv[1]
    if not os.path.isfile(image_path):
        sys.exit(
            f"Image not found: {image_path}\n"
            "Tip: pass a path relative to backend/ without a leading slash, e.g.\n"
            "    ../.venv/bin/python scripts/try_cost_to_buy.py "
            "app/sections/cost_to_buy/test_image.jpg"
        )
    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"

    with httpx.Client(timeout=60.0) as client:
        # 1) Read the product name + price from the image.
        with open(image_path, "rb") as fh:
            files = {"file": (image_path.rsplit("/", 1)[-1], fh, mime)}
            resp = client.post(f"{BASE_URL}/extract", files=files)
        print(f"POST /extract -> {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            return
        data = resp.json()
        print("  product_name:", data.get("product_name"))
        print("  price:", data.get("price"), data.get("currency"))
        print("  confidence:", data.get("confidence"), "| model:", data.get("model"))

        price = data.get("price")
        if price is None:
            print("\nNo legible price in the image; not running the cost step.")
            return

        # 2) Extra cost of adding this purchase at the current monthly payment.
        payload = {**CARD, "purchase_amount": price}
        resp = client.post(f"{BASE_URL}/purchase-impact", json=payload)
        print(f"\nPOST /purchase-impact (purchase_amount={price}) -> {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
            return

        r = resp.json()
        print("  baseline payoff months:", r["baseline"]["months_to_payoff"])
        print("  with purchase months:  ", r["with_purchase"]["months_to_payoff"])
        print("  EXTRA TOTAL PAID:      ", r["currency"], r["extra_total_paid"])
        print("  extra interest:        ", r["extra_interest"])
        print("  extra months:          ", r["extra_months"])
        print("  payoff date:           ", r["with_purchase"]["payoff_date"])
        print("  scenarios (payment -> months, extra total paid):")
        for s in r["scenarios"]:
            print(
                f"    {r['currency']} {s['monthly_payment']:.2f} -> "
                f"{s['months_to_payoff']} months, extra {s['extra_total_paid']}"
            )


if __name__ == "__main__":
    main()
