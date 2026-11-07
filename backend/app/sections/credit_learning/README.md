"""Credit Learning section — lessons that teach users how credit works.

**Owner:** _fill in_ (see `.clinerules/00-project-overview.md`)

## Endpoints (`/api/v1/credit-learning`)

| Method | Path | Status |
| --- | --- | --- |
| GET | `/ping` | implemented |
| GET | `/lessons` | **stub → 501** |
| GET | `/lessons/{slug}` | **stub → 501** |

## Supabase

Table: `lessons` — suggested columns: `id`, `slug` (unique), `title`, `summary`,
`body_markdown`, `key_takeaways` (text[]), `difficulty`, `estimated_minutes`,
`is_published`, `created_at`, `updated_at`.

RLS: anon may `select` where `is_published = true`; nothing else.

## TODOs

- [ ] Create the `lessons` table + RLS policy in Supabase.
- [ ] Implement `repository.list_lessons` / `get_lesson_by_slug`.
- [ ] Implement `service.list_lessons` / `get_lesson` (raise `NotFoundError` for bad slugs).
- [ ] Write the first three lessons (start with APR and minimum payments).
