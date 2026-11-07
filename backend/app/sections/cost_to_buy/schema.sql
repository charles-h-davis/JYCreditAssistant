-- Cost to Buy schema — run once in the Supabase SQL editor.
-- Run AFTER backend/app/sections/card_storage/schema.sql: purchase_plans.card_id
-- and card_payment_settings.card_id reference public.credit_cards.
--
-- Creates:
--   purchase_plans        one row per confirmed purchase the user plans to make.
--   card_payment_settings the CURRENT monthly payment per card (no history kept).
--
-- Money is numeric(12,2); everything is GBP by default.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- purchase_plans
-- ---------------------------------------------------------------------------
create table if not exists public.purchase_plans (
    id               uuid primary key default gen_random_uuid(),
    user_id          uuid not null,
    card_id          uuid not null references public.credit_cards (id) on delete cascade,
    product_name     text,
    purchase_amount  numeric(12,2) not null check (purchase_amount > 0),
    currency         text not null default 'GBP',
    monthly_payment  numeric(12,2) not null check (monthly_payment > 0),
    months_to_payoff integer check (months_to_payoff is null or months_to_payoff >= 0),
    total_interest   numeric(12,2) check (total_interest is null or total_interest >= 0),
    created_at       timestamptz not null default now()
);

create index if not exists purchase_plans_user_id_idx on public.purchase_plans (user_id);
create index if not exists purchase_plans_card_id_idx on public.purchase_plans (card_id);

-- ---------------------------------------------------------------------------
-- card_payment_settings: the current monthly payment for one card.
-- ---------------------------------------------------------------------------
create table if not exists public.card_payment_settings (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid not null,
    card_id         uuid not null references public.credit_cards (id) on delete cascade,
    monthly_payment numeric(12,2) not null check (monthly_payment > 0),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    unique (user_id, card_id)
);

create index if not exists card_payment_settings_user_id_idx
    on public.card_payment_settings (user_id);

-- ---------------------------------------------------------------------------
-- updated_at trigger
-- ---------------------------------------------------------------------------
create or replace function public.cost_to_buy_set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists card_payment_settings_set_updated_at
    on public.card_payment_settings;
create trigger card_payment_settings_set_updated_at
    before update on public.card_payment_settings
    for each row execute function public.cost_to_buy_set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security — each user only sees and writes their own rows.
-- (The backend uses the service-role key because there is no JWT auth dependency
-- yet; repository queries still filter on user_id.)
-- ---------------------------------------------------------------------------
alter table public.purchase_plans enable row level security;
alter table public.card_payment_settings enable row level security;

drop policy if exists purchase_plans_select_own on public.purchase_plans;
create policy purchase_plans_select_own on public.purchase_plans
    for select using (user_id = auth.uid());

drop policy if exists purchase_plans_insert_own on public.purchase_plans;
create policy purchase_plans_insert_own on public.purchase_plans
    for insert with check (user_id = auth.uid());

drop policy if exists purchase_plans_update_own on public.purchase_plans;
create policy purchase_plans_update_own on public.purchase_plans
    for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists purchase_plans_delete_own on public.purchase_plans;
create policy purchase_plans_delete_own on public.purchase_plans
    for delete using (user_id = auth.uid());

drop policy if exists card_payment_settings_select_own
    on public.card_payment_settings;
create policy card_payment_settings_select_own on public.card_payment_settings
    for select using (user_id = auth.uid());

drop policy if exists card_payment_settings_insert_own
    on public.card_payment_settings;
create policy card_payment_settings_insert_own on public.card_payment_settings
    for insert with check (user_id = auth.uid());

drop policy if exists card_payment_settings_update_own
    on public.card_payment_settings;
create policy card_payment_settings_update_own on public.card_payment_settings
    for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists card_payment_settings_delete_own
    on public.card_payment_settings;
create policy card_payment_settings_delete_own on public.card_payment_settings
    for delete using (user_id = auth.uid());
