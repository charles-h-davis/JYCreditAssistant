"""Screenshot every screen of the mobile app with Playwright.

Usage (from the repo root, with the API on :8000 and `npm run dev` on :3000):

    .venv\\Scripts\\python.exe frontend\\scripts\\screenshot.py

Output: frontend/screenshots/NN-name.png at 390x844 @2x (iPhone 14/15 size).
"""

import asyncio
import sys
from pathlib import Path
from urllib.request import urlopen

from playwright.async_api import Page, async_playwright

BASE = "http://localhost:3000"
API_HEALTH = "http://127.0.0.1:8000/health"
OUT = Path(__file__).resolve().parents[1] / "screenshots"
VIEWPORT = {"width": 390, "height": 844}

ROUTES = [
    ("03-transactions", "/transactions"),
    ("04-learning", "/learning"),
    ("05-account", "/account"),
    ("06-purchase", "/purchase"),
    ("07-purchase-photo", "/purchase/photo"),
    ("08-purchase-details", "/purchase/details"),
    ("09-assistant", "/assistant"),
]


async def shot(page: Page, name: str) -> None:
    await page.screenshot(path=str(OUT / f"{name}.png"))
    print(f"  saved {name}.png")


def api_is_up() -> bool:
    try:
        with urlopen(API_HEALTH, timeout=3) as response:  # noqa: S310 - local dev probe
            return response.status == 200
    except OSError:
        return False


async def main() -> int:
    if not api_is_up():
        print(f"API is not answering on {API_HEALTH} — start uvicorn first.")
        return 1

    OUT.mkdir(exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            locale="en-GB",
            timezone_id="Europe/London",
        )
        page = await context.new_page()
        page.on("console", lambda message: print(f"    [console:{message.type}] {message.text}"))

        print("sign-in")
        await page.goto(f"{BASE}/sign-in", wait_until="networkidle")
        await shot(page, "01-sign-in")

        print("dashboard")
        await page.get_by_role("button", name="Continue with the demo account").click()
        await page.wait_for_url("**/dashboard", timeout=90_000)
        await page.wait_for_timeout(3_000)
        await shot(page, "02-dashboard")

        print("chart swipe")
        pager = page.get_by_test_id("chart-pager")
        selected_dot = pager.locator('[role="tab"][aria-selected="true"]')
        before = await selected_dot.first.get_attribute("aria-label")
        box = await pager.bounding_box()
        if box:
            centre_x = box["x"] + box["width"] / 2
            centre_y = box["y"] + box["height"] / 2
            await page.mouse.move(centre_x, centre_y)
            await page.mouse.down()
            for step in range(1, 13):
                await page.mouse.move(centre_x - step * 12, centre_y)
            await page.mouse.up()
            await page.wait_for_timeout(900)
        after = await selected_dot.first.get_attribute("aria-label")
        print(f"  {'PASS' if before != after else 'FAIL'} chart swipe: {before!r} -> {after!r}")

        print("transaction months")
        await page.goto(f"{BASE}/transactions", wait_until="networkidle")
        await page.wait_for_timeout(1_800)
        await shot(page, "03-transactions")
        next_button = page.get_by_role("button", name="Next month")
        print(f"  next disabled on the newest month: {await next_button.is_disabled()}")
        await page.get_by_role("button", name="Previous month").click()
        await page.wait_for_timeout(700)
        month_label = page.locator("section p.text-sm.font-medium").first
        print(f"  after Previous -> {await month_label.inner_text()!r}")
        print(f"  next enabled after going back: {await next_button.is_enabled()}")
        await shot(page, "03b-transactions-previous")

        print("category chips drag")
        strip = page.locator('[role="group"][aria-label="Filter by category"]').first
        await strip.scroll_into_view_if_needed()
        strip_box = await strip.bounding_box()
        if strip_box:
            start_x = strip_box["x"] + strip_box["width"] - 30
            start_y = strip_box["y"] + strip_box["height"] / 2
            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            for step in range(1, 11):
                await page.mouse.move(start_x - step * 14, start_y)
            await page.mouse.up()
            await page.wait_for_timeout(500)
        scrolled = await strip.evaluate("el => el.scrollLeft")
        print(f"  {'PASS' if scrolled > 0 else 'FAIL'} chips dragged to {scrolled}px")
        await shot(page, "03c-transactions-chips-scrolled")

        for name, route in ROUTES:
            print(route)
            await page.goto(f"{BASE}{route}", wait_until="networkidle")
            await page.wait_for_timeout(1_800)
            if route == "/purchase/details":
                await shot(page, name)
                await page.locator("#product-name").fill("H&M Grey Suit")
                await page.locator("#product-price").fill("123.45")
                await page.get_by_role("button", name="Confirm").click()
                await page.wait_for_url("**/purchase/plan", timeout=20_000)
                await page.wait_for_timeout(1_500)
                await shot(page, "10-purchase-plan")
                continue
            await shot(page, name)

        print("lesson flow")
        await page.goto(f"{BASE}/learning", wait_until="networkidle")
        await page.wait_for_timeout(1_500)
        nodes = page.locator("button[aria-label*='lessons complete']")
        if await nodes.count() > 2:
            await nodes.nth(2).click()
            await page.wait_for_timeout(900)
            await shot(page, "11-learning-sheet")
            start = page.get_by_role("link", name="Start lesson")
            if await start.count() > 0:
                await start.first.click()
                await page.wait_for_timeout(2_500)
                await shot(page, "12-lesson-summary")
                await page.get_by_role("button", name="Start questions").click()
                await page.wait_for_timeout(700)
                options = page.locator("main button[aria-pressed]")
                if await options.count() > 1:
                    await options.nth(1).click()
                    await page.wait_for_timeout(400)
                await shot(page, "13-lesson-question")

        print("dashboard chart: net spending bars")
        await page.goto(f"{BASE}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(2_000)
        bars = page.get_by_role("tab", name="Net spending")
        if await bars.count() > 0:
            await bars.first.click()
            await page.wait_for_timeout(700)
            await shot(page, "14-dashboard-net-spending")

        print("dashboard chart: payoff projection")
        payoff = page.get_by_role("tab", name="Balance to debt free")
        if await payoff.count() > 0:
            await payoff.first.click()
            await page.wait_for_timeout(700)
            await shot(page, "15-dashboard-payoff")

        print("dashboard repayment slider")
        await page.goto(f"{BASE}/dashboard", wait_until="networkidle")
        await page.wait_for_timeout(2_000)
        tile = page.locator("button", has_text="Monthly Repayment").first
        if await tile.count() > 0:
            await tile.click()
            await page.wait_for_timeout(1_200)
            slider = page.locator('input[type="range"]').first
            if await slider.count() > 0:
                await slider.focus()
                for _ in range(30):
                    await page.keyboard.press("ArrowRight")
                await page.wait_for_timeout(600)
            await shot(page, "16-repayment-slider")

        await context.close()
        await browser.close()

    print(f"\nScreenshots written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
