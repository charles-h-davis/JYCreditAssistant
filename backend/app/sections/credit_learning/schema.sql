-- Credit Learning schema — run once in the Supabase SQL editor.
-- Creates the roadmap content (categories -> lessons -> questions) plus the
-- per-user progress, attempts and streak tables.
--
-- Content tables are public read-only; user tables are scoped to the owner.
-- The backend currently uses the service-role key (no JWT auth yet) and filters
-- every query by user_id; see TODO in router.py.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Content: categories (5) -> lessons (3 each) -> questions (5 each)
-- ---------------------------------------------------------------------------
create table if not exists public.learning_categories (
    id         text primary key,
    title      text not null,
    position   smallint not null check (position between 1 and 5),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.learning_lessons (
    id           uuid primary key default gen_random_uuid(),
    slug         text not null unique,
    category_id  text not null references public.learning_categories (id) on delete cascade,
    position     smallint not null check (position between 1 and 3),
    title        text not null,
    summary      text not null,
    is_published boolean not null default true,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now(),
    unique (category_id, position)
);

create table if not exists public.learning_questions (
    id            uuid primary key default gen_random_uuid(),
    lesson_id     uuid not null references public.learning_lessons (id) on delete cascade,
    position      smallint not null check (position between 1 and 5),
    prompt        text not null,
    options       jsonb not null
                  check (jsonb_typeof(options) = 'array' and jsonb_array_length(options) = 4),
    correct_index smallint not null check (correct_index between 0 and 3),
    explanation   text,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    unique (lesson_id, position)
);

create index if not exists learning_lessons_category_idx
    on public.learning_lessons (category_id);
create index if not exists learning_questions_lesson_idx
    on public.learning_questions (lesson_id);

-- ---------------------------------------------------------------------------
-- User progress
-- ---------------------------------------------------------------------------
create table if not exists public.learning_completions (
    id                 uuid primary key default gen_random_uuid(),
    user_id            uuid not null,
    lesson_id          uuid not null references public.learning_lessons (id) on delete cascade,
    attempts           integer not null default 1 check (attempts >= 1),
    last_score         smallint not null check (last_score >= 0),
    best_score         smallint not null check (best_score >= 0),
    first_completed_at timestamptz not null default now(),
    last_completed_at  timestamptz not null default now(),
    unique (user_id, lesson_id)
);

create table if not exists public.learning_attempts (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null,
    kind         text not null check (kind in ('lesson', 'recap')),
    lesson_id    uuid references public.learning_lessons (id) on delete set null,
    question_ids uuid[] not null default '{}',
    score        smallint not null check (score >= 0),
    total        smallint not null check (total >= 1),
    created_at   timestamptz not null default now()
);

create table if not exists public.learning_streaks (
    user_id            uuid primary key,
    current_streak     integer not null default 0 check (current_streak >= 0),
    longest_streak     integer not null default 0 check (longest_streak >= 0),
    last_activity_date date,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now()
);

create index if not exists learning_completions_user_idx
    on public.learning_completions (user_id);
create index if not exists learning_attempts_user_idx
    on public.learning_attempts (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- updated_at maintenance
-- ---------------------------------------------------------------------------
create or replace function public.credit_learning_set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists learning_categories_set_updated_at on public.learning_categories;
create trigger learning_categories_set_updated_at
    before update on public.learning_categories
    for each row execute function public.credit_learning_set_updated_at();

drop trigger if exists learning_lessons_set_updated_at on public.learning_lessons;
create trigger learning_lessons_set_updated_at
    before update on public.learning_lessons
    for each row execute function public.credit_learning_set_updated_at();

drop trigger if exists learning_questions_set_updated_at on public.learning_questions;
create trigger learning_questions_set_updated_at
    before update on public.learning_questions
    for each row execute function public.credit_learning_set_updated_at();

drop trigger if exists learning_streaks_set_updated_at on public.learning_streaks;
create trigger learning_streaks_set_updated_at
    before update on public.learning_streaks
    for each row execute function public.credit_learning_set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security
--
-- Content: anyone may read the published catalogue; only the service role
-- (seed script) writes it.
-- User tables: each user only sees and writes their own rows.
-- ---------------------------------------------------------------------------
alter table public.learning_categories enable row level security;
alter table public.learning_lessons enable row level security;
alter table public.learning_questions enable row level security;
alter table public.learning_completions enable row level security;
alter table public.learning_attempts enable row level security;
alter table public.learning_streaks enable row level security;

drop policy if exists learning_categories_read on public.learning_categories;
create policy learning_categories_read on public.learning_categories
    for select using (true);

drop policy if exists learning_lessons_read on public.learning_lessons;
create policy learning_lessons_read on public.learning_lessons
    for select using (is_published);

drop policy if exists learning_questions_read on public.learning_questions;
create policy learning_questions_read on public.learning_questions
    for select using (
        exists (
            select 1
            from public.learning_lessons lesson
            where lesson.id = learning_questions.lesson_id
              and lesson.is_published
        )
    );

drop policy if exists learning_completions_own on public.learning_completions;
create policy learning_completions_own on public.learning_completions
    for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists learning_attempts_select_own on public.learning_attempts;
create policy learning_attempts_select_own on public.learning_attempts
    for select using (user_id = auth.uid());

drop policy if exists learning_attempts_insert_own on public.learning_attempts;
create policy learning_attempts_insert_own on public.learning_attempts
    for insert with check (user_id = auth.uid());

drop policy if exists learning_attempts_delete_own on public.learning_attempts;
create policy learning_attempts_delete_own on public.learning_attempts
    for delete using (user_id = auth.uid());

drop policy if exists learning_streaks_own on public.learning_streaks;
create policy learning_streaks_own on public.learning_streaks
    for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Optional, once every user_id you send is a real auth.users row:
-- alter table public.learning_completions
--     add constraint learning_completions_user_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;
-- alter table public.learning_attempts
--     add constraint learning_attempts_user_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;
-- alter table public.learning_streaks
--     add constraint learning_streaks_user_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;
