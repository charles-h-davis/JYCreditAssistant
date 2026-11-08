-- Friends Feed schema — run once in the Supabase SQL editor.
--
-- Run this AFTER backend/app/sections/credit_learning/schema.sql: the feed is
-- written by the browser right after a lesson attempt has been graded.
--
-- Creates:
--   friends_feed_entries  one row per feed event. Two kinds of row live here:
--                         the user's own finished lesson / refresh round
--                         (actor = 'You', written by the app) and their friends'
--                         activity (actor = the friend's name, written once by
--                         app/sections/friends_feed/seed.py). Append-only — the
--                         feed shows the newest rows first.
--
-- Nothing is generated at request time: GET /feed is a plain read of this table,
-- so the feed keeps working (and keeps its history) without any hardcoded data.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- friends_feed_entries
-- ---------------------------------------------------------------------------
create table if not exists public.friends_feed_entries (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null,
    kind       text not null check (kind in ('lesson', 'recap', 'streak')),
    actor      text not null default 'You',
    action     text not null,
    detail     text,
    created_at timestamptz not null default now()
);

create index if not exists friends_feed_entries_user_idx
    on public.friends_feed_entries (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security
--
-- Each user reads and writes only their own entries. The backend currently uses
-- the service-role key (no JWT auth yet), which bypasses these policies; they
-- are here so the anon client can be used once auth lands.
-- ---------------------------------------------------------------------------
alter table public.friends_feed_entries enable row level security;

drop policy if exists friends_feed_entries_select_own on public.friends_feed_entries;
create policy friends_feed_entries_select_own on public.friends_feed_entries
    for select using (user_id = auth.uid());

drop policy if exists friends_feed_entries_insert_own on public.friends_feed_entries;
create policy friends_feed_entries_insert_own on public.friends_feed_entries
    for insert with check (user_id = auth.uid());

drop policy if exists friends_feed_entries_delete_own on public.friends_feed_entries;
create policy friends_feed_entries_delete_own on public.friends_feed_entries
    for delete using (user_id = auth.uid());

-- Optional, once every user_id you send is a real auth.users row:
-- alter table public.friends_feed_entries
--     add constraint friends_feed_entries_user_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;

-- Handy for demos: wipe the demo user's feed history.
-- delete from public.friends_feed_entries where user_id = '<demo-user-uuid>';
