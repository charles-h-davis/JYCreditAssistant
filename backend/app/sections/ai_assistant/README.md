"""AI Credit Assistant section — conversational credit help.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/ai-assistant`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| POST | `/chat` | **stub → 501** |

## Files

- `prompts/system_prompt.md` — the assistant's guardrails. Versioned here on purpose:
  prompt changes are code changes and get reviewed. Loaded by
  `service.build_system_prompt()`.
- `service.py` — prompt assembly + model call + reply shaping.
- `repository.py` — conversation persistence.

## Supabase

Tables:

- `chat_sessions` — `id` (uuid pk), `user_id` (uuid, fk → `auth.users`), `title`,
  `created_at`, `updated_at`.
- `chat_messages` — `id` (uuid pk), `session_id` (uuid, fk → `chat_sessions`),
  `role` (text: system/user/assistant), `content` (text), `created_at`.

RLS: `user_id = auth.uid()` on `chat_sessions`; on `chat_messages`, join to the session.

## Rules

- Ground answers in the user's real cards — read them via the Card Storage section,
  never by querying `credit_cards` from here.
- Provider key comes from `settings.openai_api_key`; never hardcode or log it.
- Log prompts/responses at debug level only, and never log full user financial detail.

## TODOs

- [ ] Decide the model + provider (OpenAI is already in requirements).
- [ ] Create `chat_sessions` / `chat_messages` + RLS.
- [ ] Implement `repository` → `service.generate_reply` → wire `POST /chat`.
- [ ] Add streaming (SSE) once the non-streaming path works.
