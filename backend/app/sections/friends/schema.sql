-- Friends schema — run once in the Supabase SQL editor.
--
-- Creates:
--   friends  one row per friend a user has added: a display name plus an email,
--            unique per user. A "friend" here is a contact the user owns — it does
--            NOT have to be a CreditMate auth user, so adding an address never
--            fails and no fictional accounts are created.
--
-- Run AFTER backend/app/sections/friends_feed/schema.sql if you want the whole
-- social feature; the two sections own separate tables.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- friends
-- ---------------------------------------------------------------------------
create table if not exists public.friends (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null,
    friend_name  text not null,
    friend_email text not null check (position('@' in friend_email) > 1),
    created_at   timestamptz not null default now(),
    unique (user_id, friend_email)
);

create index if not exists friends_user_idx
    on public.friends (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security
--
-- Each user reads and writes only their own friends. The backend currently uses
-- the service-role key (no JWT auth yet), which bypasses these policies; they are
-- here so the anon client can be used once auth lands.
-- ---------------------------------------------------------------------------
alter table public.friends enable row level security;

drop policy if exists friends_select_own on public.friends;
create policy friends_select_own on public.friends
    for select using (user_id = auth.uid());

drop policy if exists friends_insert_own on public.friends;
create policy friends_insert_own on public.friends
    for insert with check (user_id = auth.uid());

drop policy if exists friends_delete_own on public.friends;
create policy friends_delete_own on public.friends
    for delete using (user_id = auth.uid());

-- Optional, once every user_id you send is a real auth.users row:
-- alter table public.friends
--     add constraint friends_user_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;

-- Handy for demos: start over for one user.
-- delete from public.friends where user_id = '<demo-user-uuid>';
