-- Notifications schema — run once in the Supabase SQL editor.
--
-- Run AFTER card_storage/schema.sql and cost_to_buy/schema.sql: this section
-- reads `card_transactions` and `purchase_plans`, and only owns the table below.
--
-- Creates:
--   purchase_match_dismissals  the (plan, transaction) pairs the user answered
--                              with ✗, so the same match never notifies twice.
--
-- There is deliberately NO foreign key to purchase_plans / card_transactions:
-- a dismissed pair must stay remembered even after the plan is deleted.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- purchase_match_dismissals
-- ---------------------------------------------------------------------------
create table if not exists public.purchase_match_dismissals (
    id             uuid primary key default gen_random_uuid(),
    user_id        uuid not null,
    plan_id        uuid not null,
    transaction_id uuid not null,
    created_at     timestamptz not null default now(),
    unique (user_id, plan_id, transaction_id)
);

create index if not exists purchase_match_dismissals_user_idx
    on public.purchase_match_dismissals (user_id);

-- ---------------------------------------------------------------------------
-- Row Level Security
--
-- Each user reads and writes only their own dismissals. The backend currently
-- uses the service-role key (no JWT auth yet), which bypasses these policies;
-- they are here so the anon client can be used once auth lands.
-- ---------------------------------------------------------------------------
alter table public.purchase_match_dismissals enable row level security;

drop policy if exists purchase_match_dismissals_select_own
    on public.purchase_match_dismissals;
create policy purchase_match_dismissals_select_own on public.purchase_match_dismissals
    for select using (user_id = auth.uid());

drop policy if exists purchase_match_dismissals_insert_own
    on public.purchase_match_dismissals;
create policy purchase_match_dismissals_insert_own on public.purchase_match_dismissals
    for insert with check (user_id = auth.uid());

drop policy if exists purchase_match_dismissals_delete_own
    on public.purchase_match_dismissals;
create policy purchase_match_dismissals_delete_own on public.purchase_match_dismissals
    for delete using (user_id = auth.uid());

-- Optional, once every user_id you send is a real auth.users row:
-- alter table public.purchase_match_dismissals
--     add constraint purchase_match_dismissals_user_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;

-- Handy for demos: let every match notify again.
-- delete from public.purchase_match_dismissals where user_id = '<demo-user-uuid>';
