"""AI Credit Assistant section — conversational credit help.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

One question in, one concise plain-English answer out, powered by Gemini. Strictly
scope-limited to credit and money topics: anything else gets a fixed refusal.

## Endpoints (`/api/v1/ai-assistant`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| POST | `/chat` | implemented |

`POST /chat` body: `{"message": "..."}` (1–2000 chars, trimmed).

Response:

```json
{
  "reply": "Pay the **highest APR** card first...\nFor more, see the lesson \"Interest and APR\".",
  "in_scope": true,
  "refused": false,
  "model": "gemini-3.5-flash-lite"
}
```

- Off-topic question → `200` with `reply = "I can't answer that. I can only help with
  credit and money questions."`, `in_scope: false`, `refused: true`.
- Missing `GEMINI_API_KEY` → `503 gemini_not_configured`.
- Gemini error / malformed reply → `502 upstream_error`.

## How scope is enforced

Gemini is asked (via `responseMimeType`/`responseSchema`) to return JSON
`{"in_scope": bool, "answer": str}` in the same call that answers:

- The system prompt lists the allowed topics and the out-of-scope categories.
- `in_scope: false` never leaks model text: the service returns its own fixed refusal.
- An in-scope question with an empty answer returns a "please rephrase" fallback.

The prompt also receives the **Credit Learning lesson catalogue** (titles + slugs) so
answers can say `For more, see the lesson "<title>"` using only real lessons.

## Files

- `prompts/system_prompt.md` — versioned guardrails + scope + output contract.
- `gemini_client.py` — thin Gemini REST client (`generateContent`, JSON schema), key
  sent as `x-goog-api-key` so it never appears in request logs.
- `service.py` — prompt assembly, refusal/fallback shaping.
- `repository.py` — unchanged scaffold; conversation persistence is deferred
  (see TODOs), so no tables are required.

## Environment

`GEMINI_API_KEY` and `GEMINI_MODEL` in `backend/.env` (already documented in
`.env.example`). Default model: `gemini-3.5-flash-lite`.

## TODOs

- [ ] Persist conversations (`chat_sessions` / `chat_messages`) so the UI can load history.
- [ ] Optionally ground answers in the user's own cards via the Card Storage service.
- [ ] Streaming (SSE) once the non-streaming path is proven.
- [ ] Rate limiting per user once auth exists.

