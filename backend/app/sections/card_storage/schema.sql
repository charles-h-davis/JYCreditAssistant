-- Card Storage schema — run once in the Supabase SQL editor.
-- Creates: plaid_items (access tokens), credit_cards, card_transactions.
--
-- Field naming follows the product wording:
--   closing_day   = day of month the statement CLOSES (statement day)
--   statement_day = day of month the payment is DUE     (due date)
--
-- Money is numeric(12,2). Amounts keep Plaid's sign convention: positive means
-- money left the account (a purchase).

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- plaid_items: one row per linked Plaid Item. Holds the long-lived access
-- token, so this table is backend-only: RLS is enabled with NO anon policies
-- and only the service-role key (used by the backend) can read or write it.
-- ---------------------------------------------------------------------------
create table if not exists public.plaid_items (
    id                  uuid primary key default gen_random_uuid(),
    user_id             uuid not null,
    item_id             text not null unique,
    access_token        text not null,
    institution_id      text,
    institution_name    text,
    transactions_cursor text,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- credit_cards: manual cards plus cards loaded from Plaid.
-- A manual card has NULL plaid_item_id / plaid_account_id.
-- Upserts key on (user_id, plaid_account_id).
-- ---------------------------------------------------------------------------
create table if not exists public.credit_cards (
    id                uuid primary key default gen_random_uuid(),
    user_id           uuid not null,
    plaid_item_id     uuid references public.plaid_items (id) on delete set null,
    plaid_account_id  text,
    nickname          text not null,
    issuer            text not null,
    last_four         char(4) not null check (last_four ~ '^[0-9]{4}$'),
    credit_limit      numeric(12,2) check (credit_limit is null or credit_limit > 0),
    -- Plaid can report negative current/available balances (overpayment,
    -- over-limit), so only the manual API payload enforces >= 0.
    current_balance   numeric(12,2) not null default 0,
    available_balance numeric(12,2),
    purchase_apr      numeric(5,2)
                      check (purchase_apr is null or (purchase_apr >= 0 and purchase_apr <= 100)),
    closing_day       smallint check (closing_day is null or (closing_day between 1 and 31)),
    statement_day     smallint check (statement_day is null or (statement_day between 1 and 31)),
    is_secured        boolean not null default false,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now(),
    unique (user_id, plaid_account_id)
);

create index if not exists credit_cards_user_id_idx on public.credit_cards (user_id);

-- ---------------------------------------------------------------------------
-- card_transactions: Plaid transaction history, keyed by transaction id.
-- ---------------------------------------------------------------------------
create table if not exists public.card_transactions (
    id                   uuid primary key default gen_random_uuid(),
    user_id              uuid not null,
    card_id              uuid not null references public.credit_cards (id) on delete cascade,
    plaid_transaction_id text not null unique,
    description          text,
    merchant_name        text,
    amount               numeric(12,2) not null,
    category             text,
    authorized_date      date,
    posted_date          date,
    pending              boolean not null default false,
    iso_currency_code    char(3),
    created_at           timestamptz not null default now(),
    updated_at           timestamptz not null default now()
);

create index if not exists card_transactions_card_id_idx
    on public.card_transactions (card_id, posted_date desc);
create index if not exists card_transactions_user_id_idx
    on public.card_transactions (user_id);

-- ---------------------------------------------------------------------------
-- updated_at maintenance
-- ---------------------------------------------------------------------------
create or replace function public.card_storage_set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists credit_cards_set_updated_at on public.credit_cards;
create trigger credit_cards_set_updated_at
    before update on public.credit_cards
    for each row execute function public.card_storage_set_updated_at();

drop trigger if exists card_transactions_set_updated_at on public.card_transactions;
create trigger card_transactions_set_updated_at
    before update on public.card_transactions
    for each row execute function public.card_storage_set_updated_at();

drop trigger if exists plaid_items_set_updated_at on public.plaid_items;
create trigger plaid_items_set_updated_at
    before update on public.plaid_items
    for each row execute function public.card_storage_set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security
--
-- credit_cards / card_transactions: each user only sees and writes their rows.
-- plaid_items: RLS on, no policies -> anon/authenticated denied, service role
-- only. (The backend currently uses the service-role key because there is no
-- JWT auth dependency yet; repository queries still filter on user_id.)
-- ---------------------------------------------------------------------------
alter table public.credit_cards enable row level security;
alter table public.card_transactions enable row level security;
alter table public.plaid_items enable row level security;

drop policy if exists credit_cards_select_own on public.credit_cards;
create policy credit_cards_select_own on public.credit_cards
    for select using (user_id = auth.uid());

drop policy if exists credit_cards_insert_own on public.credit_cards;
create policy credit_cards_insert_own on public.credit_cards
    for insert with check (user_id = auth.uid());

drop policy if exists credit_cards_update_own on public.credit_cards;
create policy credit_cards_update_own on public.credit_cards
    for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists credit_cards_delete_own on public.credit_cards;
create policy credit_cards_delete_own on public.credit_cards
    for delete using (user_id = auth.uid());

drop policy if exists card_transactions_select_own on public.card_transactions;
create policy card_transactions_select_own on public.card_transactions
    for select using (user_id = auth.uid());

drop policy if exists card_transactions_insert_own on public.card_transactions;
create policy card_transactions_insert_own on public.card_transactions
    for insert with check (user_id = auth.uid());

drop policy if exists card_transactions_update_own on public.card_transactions;
create policy card_transactions_update_own on public.card_transactions
    for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists card_transactions_delete_own on public.card_transactions;
create policy card_transactions_delete_own on public.card_transactions
    for delete using (user_id = auth.uid());

-- Optional, once you create the auth users: enforce ownership at the FK level
-- as well. Uncomment only if every user_id you send is a real auth.users row.
-- alter table public.plaid_items
--     add constraint plaid_items_user_id_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;
-- alter table public.credit_cards
--     add constraint credit_cards_user_id_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;
-- alter table public.card_transactions
--     add constraint card_transactions_user_id_fkey
--     foreign key (user_id) references auth.users (id) on delete cascade;
