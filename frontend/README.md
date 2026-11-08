# Frontend — CreditMate (Next.js mobile web app)

Mobile-first React app for CreditMate: sign in, dashboard, transactions,
credit learning, purchase checker and the AI assistant. It talks to the FastAPI
backend in `backend/`; **all** credit data goes through the API. Supabase is used
only for auth, with the public anon key.

## Run it

```powershell
cd frontend
npm install
copy .env.local.example .env.local   # then fill in the Supabase URL + anon key
npm run dev                          # http://localhost:3000
```

Start the API first (`backend/`, port 8000) and seed the demo account:

```powershell
cd backend
..\.venv\Scripts\python.exe -m app.sections.credit_learning.seed
..\.venv\Scripts\python.exe scripts\seed_demo.py
```

Demo login: `demo@demo.com` / `demo123!` (the sign-in screen has a one-tap button).

> **One-time SQL:** the Cost to Buy tables must exist before monthly repayments and
> planned purchases work. Run `backend/app/sections/cost_to_buy/schema.sql` in the
> Supabase SQL editor. Until then those endpoints return PGRST205 and the UI shows
> the API error. The same applies to the social feature — run
> `backend/app/sections/friends_feed/schema.sql` (feed) and
> `backend/app/sections/friends/schema.sql` (friend list), then
> `python -m app.sections.friends.seed` to load the demo friends. The dashboard's
> notification bell needs `backend/app/sections/notifications/schema.sql`.

> **Turbopack:** this machine only has Turbopack's WASM bindings, so `dev`/`build`
> pass `--webpack`. Drop the flag on a platform with native Turbopack support.

> **Deployed API URL:** in a production build the app talks to the same-origin
> `/api/v1` instead of `http://127.0.0.1:8000/api/v1` — the root `vercel.json` rewrites
> `/api/(.*)` to the `backend` service. See the deployment section of the repo README.

## Scripts

```powershell
npm run dev        # dev server
npm run build      # production build
npm run lint       # eslint
npm run typecheck  # tsc --noEmit
```

## Structure

```
src/
  app/
    sign-in/                     sign in + create account (demo shortcut)
    (app)/                       authenticated shell (bottom nav + auth guard)
      dashboard/                 balance, debt-free date, swipeable charts, streak
      transactions/              month pager, category filter, rows
      learning/                  five activity rings, lesson runner, recap
      friends-feed/              friends feed (X returns to Learning)
      account/                   name, card details, monthly repayment, log out
      purchase/                  initial -> photo -> details -> total cost w/ slider
      assistant/                 "Ask Me Anything" chat
  components/
    layout/    AppShell, TopBar, BottomNav, CardSwitcher
    charts/    SmoothLineChart (hand-rolled SVG), ChartPager
    feed/      FeedList — the friends feed rows
    ui/        Button, Sheet, StatTile, RangeSlider, skeletons, errors
  lib/
    api/       typed fetch client + endpoint wrappers mirroring the FastAPI schemas
    finance/   amortisation port of cost_to_buy/service.py + transaction series
    state/     session (Supabase auth), cards (SWR), purchase draft (sessionStorage)
    format.ts  money/date formatting (en-GB, GBP)
design refs/   the original screens this UI was built from
prompt.txt     the product brief
```

## Design notes

- **Colour schemes:** Light (default blue-grey), Dark and Cream — dark ink on warm
  paper — plus four accents (Indigo, Ocean, Rose, Amber), picked on **Your Account →
  Appearance** with a palette icon. Every colour is a CSS variable in
  `src/app/globals.css`: `@theme` holds Light, `[data-theme="dark"|"cream"]` blocks
  swap the palette and `[data-accent="…"]` blocks swap the accent, so a token-based
  class like `bg-surface` re-themes everywhere without touching a component.
  `<html>` carries `data-theme` / `data-accent`; `lib/state/theme.tsx` keeps them in
  localStorage (external store, so no hydration mismatch) and an inline script in
  `app/layout.tsx` applies the stored scheme **before first paint** — no flash.
  Semantic tokens keep the hardcoded colours honest: `elevated` (was `bg-white`),
  `strong` (filled chips/primary button), `danger-soft`, `scrim`, `grid`,
  `chart-label`. Charts and the activity rings read `var(--color-…)`, never literals.
- **Read aloud:** lessons and refresh rounds get a speaker button beside the exit X
  (`lib/use-speech.ts`, the browser's `speechSynthesis`, en-GB voice preferred). One
  press reads the summary, or the question plus its options; a second press pauses,
  a third resumes. If audio is on when the learner answers, the verdict and its
  explanation are read too. Speech stops on every question/phase change, and the
  button is hidden where the API isn't available.
- One 430px column on desktop, full-bleed on a phone, with safe-area padding.
- Five-item bottom nav on every screen; the current section is a soft-filled tile.
  There is **no "+" button** in the top bar — the nav's *Check Purchase* tab is the
  way in.
- **Card switching is the ‹ › pills only** (dashboard, transactions, purchase). No
  page-level swipe, so the gestures never fight the month/chart pagers.
- **Transactions** list months oldest → newest, so the current month sits on the right
  and ‹ steps back to the previous one. The arrows (or the dots) are the only control —
  no swipe. Each month shows its closing balance derived from the card's current
  balance, so the history adds up to the number on the dashboard. The category chips
  scroll sideways: drag them with the mouse, spin the wheel over them, or swipe on a
  touch screen — edge fades show there is more in either direction.
- **Charts**: balance, spend and payoff are smooth cumulative lines; *net spending* is
  a per-day bar chart (payments below the zero line). Swipe the chart card, or tap the
  dots, to move between charts. X-axis labels only carry a year where the timeline
  crosses one, and only at the tick where it changes.
- **Every monthly-payment slider** (dashboard sheet + purchase cost screen) starts at
  that card's stored repayment, bottoms out at the minimum payment — the lowest amount
  that still clears the balance — and tops out at the whole balance, i.e. debt free in
  one month with no interest. A dragged value belongs to the card it was dragged on:
  switch cards and the slider snaps back to that card's own repayment.
- **Learning** grades each answer on tap (`POST /questions/{id}/answer`) and shows the
  explanation immediately; lesson payloads still withhold the answers. Each activity
  ring carries its section title beside it (left or right, whichever side has room),
  and the ring segments show how many of that section's three lessons are done.
- `lib/finance/credit.ts` is a line-for-line port of the backend amortisation —
  if you change one, change the other.
