# Frontend (phase 2 — not started)

Next.js + React + Tailwind mobile-first web app. **Do not scaffold this yet**: the
backend contract comes first, and everything in `backend/` is still being implemented.

When we start:

```powershell
npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir
```

Planned wiring to the backend:

- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1` (see `backend/.env.example`)
- Only the Supabase **anon** key ever reaches the browser — the service-role key stays
  server-side.
- Screen map follows the backend sections: Cost to Buy → Credit Learning →
  Card Storage → AI Credit Assistant.
