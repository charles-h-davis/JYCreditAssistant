# CreditMate — Cost to Buy (Chrome extension)

Reads the price of the item you're viewing with **Gemini** (via the backend) and
shows what it really costs on your **real credit card** (via the backend), with a
slider for how changing your monthly repayment affects the total cost and time to
being debt free.

- Price extraction: screenshot → `POST /cost-to-buy/extract` (Gemini, backend).
- Card data: Supabase sign-in → `GET /card-storage/cards` + `GET /cost-to-buy/monthly-payment`.
- The maths runs **client-side** (`src/finance.js`, mirroring `frontend/.../credit.ts`)
  so the slider updates instantly without hitting the backend.

## Requirements

- Backend running from `backend/` with **`SUPABASE_URL`**, **`SUPABASE_SERVICE_ROLE_KEY`**
  and **`GEMINI_API_KEY`** set in `backend/.env` (the card/payment endpoints use the
  service role; `/extract` uses Gemini).
- The Supabase `schema.sql` files for card storage and cost-to-buy applied.
- A user account (e.g. the seeded `demo@demo.com` / `demo123!`).

## Install & configure

1. `chrome://extensions` → enable **Developer mode** → **Load unpacked** → select
   this `web_extension/` folder. Pin the icon.
2. Click the icon → **Card settings** (this opens the Options page):
   - **1. Connection** — Supabase URL, **anon key** (public), and the backend base
     URL (`http://127.0.0.1:8000/api/v1`). **Save.**
   - **2. Account** — sign in with your email/password.
   - **3. Card** — pick your card (it fetches balance, APR and monthly payment).
   - *(Optional)* **Manual fallback** — used only if the backend is unreachable.
3. Open a product page, make sure the price is **on screen**, and click the icon.

## How it works

```
click icon → capture visible tab (activeTab)
           → POST /cost-to-buy/extract  (Gemini)      → product_name, price, currency
           → (signed in) GET /card-storage/cards       → balance, APR
                        GET /cost-to-buy/monthly-payment
           → client-side maths (finance.js)           → real cost, debt-free months, slider
```

## Permissions

- `activeTab` — capture the visible tab only after you click the icon.
- `storage` — keep the connection + session + selected card locally.
- `host_permissions` — `http://localhost:8000/*`, `http://127.0.0.1:8000/*`,
  `https://*.supabase.co/*`. Fetches from the extension bypass CORS, so the backend
  needs no CORS change. Add your deployed backend origin here if you host it.

## Keys — where they go (important)

- **Supabase anon key + project URL**: enter on the Options page (public by design).
- **Service-role key + Gemini key**: **only** in `backend/.env`. Never in the
  extension.

## Maths (keep in sync)

`src/finance.js` is a direct port of `frontend/src/lib/finance/credit.ts` (which
mirrors `backend/app/sections/cost_to_buy/service.py`). Model is **payment-first**
(payment applied, then interest on the remainder; paying in full costs no interest).

Golden vector — balance **£1,800**, APR **24.99%**, item **£120**, payment **£150**:
baseline 14 mo / £243.74; with item 15 mo / £282.71; extra interest **£38.97**;
real cost (price + extra interest) **£158.97**; +1 month.

## Saving a purchase

When you're signed in with a card selected, the popup has an **Add to planned
purchases** button. It stores the item via `POST /cost-to-buy/purchase-plans` with
the current slider value as `monthly_payment`, `months_to_payoff` and
`total_interest` (extra interest). The backend also **upserts the card's monthly
payment** to that slider value, so your saved repayment changes to match — the popup
notes this under the button. Saving is disabled unless you're signed in, a card is
selected, a price was read, and the payment covers the monthly interest.

## Limitations

- Captures the **visible viewport**, so the price must be on screen (scroll, then
  press **Re-read**).
- Needs the backend running; if it's down the popup says so.
- GBP assumed (a `$`/`€` price is flagged but treated as GBP).
- The screenshot of the visible page is sent to your backend and to Gemini — a
  privacy/cost consideration (one Gemini call per read).

## Files

```
manifest.json         MV3; permissions activeTab+storage; host_permissions for backend + supabase
popup.html/.css/.js   capture → /extract → slider + results
options.html/.css/.js Connection + Account (Supabase sign-in) + Card + manual fallback
src/capture.js        captureVisibleTab → PNG Blob
src/api.js            backend calls (extract, cards, monthly payment)
src/auth.js           Supabase password login / refresh / sign-out (REST, anon key)
src/config.js         connection + selected/resolved card in chrome.storage.local
src/finance.js        amortise + helpers (client-side maths)
```

## Troubleshooting

- **503 `database_not_ready`** — a table is missing; run the section `schema.sql`.
- **"Can't reach the backend"** — start the API on :8000 (from `backend/`).
- **Sign-in failed** — check the Supabase URL + anon key in Connection settings.
- **No cards found** — the account has no cards; sync one in the app (or use the
  manual fallback).
- **"Couldn't read a price"** — scroll so the price is visible and press Re-read.
