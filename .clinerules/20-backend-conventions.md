# Backend Conventions (FastAPI + Supabase)

## Section anatomy — every section looks the same

```
backend/app/sections/<section>/
  __init__.py     # re-exports the section router: `from .router import router`
  router.py       # APIRouter only: routes, HTTP status codes, dependencies
  schemas.py      # Pydantic v2 models: request bodies, responses, DB row shapes
  service.py      # business logic; no HTTP, no direct Supabase calls
  repository.py   # every Supabase read/write for this section's tables
  README.md       # purpose, owned tables, endpoint list, TODO list
  prompts/        # (ai_assistant only) versioned LLM prompt files
```

## Layering — one direction only

`router.py` → `service.py` → `repository.py`.

- Routers never call `repository` directly and never touch `client.table(...)`.
- Services never raise `HTTPException` — they raise domain errors from
  `app.core.exceptions` (e.g. `NotFoundError`) or `ValueError`, which the routers /
  handlers translate.
- Repositories never contain business rules or HTTP concerns; they take a
  `Client` argument so tests can inject a fake.

## Supabase access

- Clients come from `app.core.database`: `get_supabase()` (anon key, RLS enforced,
  user-scoped reads) and `get_supabase_admin()` (service role, bypasses RLS — backend
  only, never expose it).
- Get a client by dependency injection, never by building one yourself:

```python
def list_cards(client: Client = Depends(get_supabase)) -> list[CreditCard]: ...
```

- Never create a client, read `os.environ`, or perform network I/O at import time.
- Settings are only read through `app.core.config.settings`.

## Async vs sync

`supabase-py` and its PostgREST calls are synchronous. So:

- Routes that hit Supabase are plain `def` — FastAPI runs them in a threadpool.
- Use `async def` only for genuinely async I/O (`httpx`, LLM streaming).
- Never block the event loop with sync I/O inside an `async def` route.

## Naming + URLs

| Thing | Convention | Example |
| --- | --- | --- |
| Python package / module | `snake_case` | `cost_to_buy` |
| Router file variable | always `router` | `router = APIRouter(...)` |
| URL path segment | `kebab-case`, plural nouns | `/api/v1/card-storage/cards` |
| Query/body fields | `snake_case` (pydantic default) | `purchase_amount` |
| Postgres tables | `snake_case`, plural | `cards`, `chat_messages` |
| Env vars | `UPPER_SNAKE_CASE` | `SUPABASE_URL` |

Set `prefix="/<section-kebab-case>"` and `tags=["<Section Name>"]` on each
`APIRouter`, and request paths relative to it. Do not hardcode `/api/v1` — `main.py`
adds the API prefix.

## Schemas

- Pydantic v2: `model_config = ConfigDict(from_attributes=True)` on DB-backed models.
- Separate inbound (`...Create` / `...Update` / `...Request`) from outbound
  (`...Response` / the entity) models. Never reuse an inbound model as a response.
- Money is `float` with values rounded to 2 decimals at the boundary; APRs are
  percentages (e.g. `24.99` means 24.99%). Document the unit in the `Field`
  description — this is a credit product, misread units are a real bug.
- Validate with `Field(..., gt=0, le=100)` and friends instead of hand-rolled checks.

## Routes

- Every section keeps a `GET /ping` returning `{"section": "<kebab-name>", "status": "ok"}`
  — it proves the router is mounted and is asserted by the smoke tests.
- Unimplemented endpoints return `501 Not Implemented` via `HTTPException`, with a
  `TODO(<section>):` comment naming the owner. Do not return fake success payloads.
- **Stub endpoints must not inject DB dependencies.** FastAPI resolves `Depends(...)`
  before the handler body runs, so a `Depends(get_supabase)` on a stub turns the 501
  into a 500 when credentials are absent and breaks the credential-free test suite.
  Add the dependency as part of implementing the endpoint.
- Declare error responses as integer keys (`responses={422: ...}`); the
  `status.HTTP_422_UNPROCESSABLE_ENTITY` constant is deprecated in current Starlette.
- Always set `summary=` and a real docstring so `/docs` is usable as the contract the
  frontend will code against.

## Tests

- One smoke test file per section: `backend/tests/sections/test_<section>.py`.
- Use the shared `client` and `api_prefix` fixtures from `backend/tests/conftest.py`.
- Tests must pass without Supabase credentials: `ping` and validation tests only.

## Style

- `ruff` for lint + import order (`python app.main`/`pytest`, `ruff check .`).
- Full type hints on public functions. No bare `except:`. No `print()` — use
  `logging.getLogger(__name__)`.
