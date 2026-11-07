"""Business logic for the Card Storage section.

The Plaid -> database mapping lives here as pure functions so it can be unit
tested without network access or Supabase (`build_card_payload`,
`build_transaction_payload`). `sync_from_plaid` orchestrates one full sync:

1. Resolve an access token (request -> `PLAID_ACCESS_TOKEN` -> fresh sandbox Item).
2. Fetch accounts + liabilities and keep the credit card accounts.
3. Upsert the Plaid Item, its cards and its transaction history.
4. Store the transactions cursor so the next sync is incremental.

Re-running a sync is idempotent: every write upserts on a natural key.
"""

import logging
import re
from datetime import date
from typing import Any

from supabase import Client

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, UpstreamServiceError
from app.sections.card_storage import repository
from app.sections.card_storage.plaid_client import PlaidClient
from app.sections.card_storage.schemas import (
    CardTransactionRead,
    CreditCardCreate,
    CreditCardRead,
    PlaidSyncRequest,
    PlaidSyncResponse,
)

logger = logging.getLogger(__name__)

#: Plaid account type whose accounts become stored cards.
CREDIT_ACCOUNT_TYPE = "credit"
#: Fallback when the issuer hides the last four digits.
UNKNOWN_LAST_FOUR = "0000"
#: APR that matters to this product; other liabilities APRs are ignored.
PURCHASE_APR_TYPE = "purchase_apr"


# --- cards -----------------------------------------------------------------


def list_cards(client: Client, *, user_id: str) -> list[CreditCardRead]:
    """Return every card stored for `user_id`."""
    rows = repository.list_cards(client, user_id=user_id)
    return [CreditCardRead.model_validate(row) for row in rows]


def create_card(client: Client, *, user_id: str, payload: CreditCardCreate) -> CreditCardRead:
    """Store a manually added card for `user_id` and return it."""
    data = payload.model_dump()
    if data["current_balance"] > data["credit_limit"]:
        raise ConflictError("current_balance cannot exceed credit_limit.")
    row = repository.insert_card(client, user_id=user_id, payload=data)
    return CreditCardRead.model_validate(row)


def list_card_transactions(
    client: Client, *, user_id: str, card_id: str
) -> list[CardTransactionRead]:
    """Return the stored transaction history for one of `user_id`'s cards."""
    if repository.get_card(client, user_id=user_id, card_id=card_id) is None:
        raise NotFoundError("Card not found.")
    rows = repository.list_transactions(client, user_id=user_id, card_id=card_id)
    return [CardTransactionRead.model_validate(row) for row in rows]


# --- pure Plaid -> row mapping ---------------------------------------------


def _money(value: Any) -> float | None:
    """Round a Plaid numeric to cents, preserving nulls."""
    if value is None:
        return None
    return round(float(value), 2)


def _day_of_month(value: str | None) -> int | None:
    """Turn a Plaid `YYYY-MM-DD` date into its day of month (1-31)."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10]).day
    except ValueError:
        logger.warning("Unparseable Plaid date %r; storing a null day of month", value)
        return None


def _purchase_apr(liability: dict[str, Any] | None) -> float | None:
    """Pick the purchase APR (percent) out of a credit liability's `aprs` list."""
    for apr in (liability or {}).get("aprs") or []:
        if apr.get("apr_type") == PURCHASE_APR_TYPE:
            percentage = apr.get("apr_percentage")
            return None if percentage is None else round(float(percentage), 2)
    return None


def _last_four(mask: str | None) -> str:
    """Return a valid four-digit mask, or a placeholder the DB will accept."""
    if mask and re.fullmatch(r"\d{4}", mask):
        return mask
    return UNKNOWN_LAST_FOUR


def build_card_payload(
    account: dict[str, Any],
    liability: dict[str, Any] | None,
    *,
    issuer: str,
) -> dict[str, Any]:
    """Map one Plaid credit account (+ its liability) to a `credit_cards` row.

    Plaid field mapping:

    - ``balances.limit``      -> ``credit_limit``
    - ``balances.current``    -> ``current_balance`` (current debt)
    - ``balances.available``  -> ``available_balance``
    - purchase APR            -> ``purchase_apr``
    - ``last_statement_issue_date`` -> ``closing_day``  (statement closes)
    - ``next_payment_due_date``     -> ``statement_day`` (payment is due)
    """
    balances = account.get("balances") or {}
    return {
        "plaid_account_id": account.get("account_id"),
        "nickname": account.get("name") or "Credit card",
        "issuer": issuer,
        "last_four": _last_four(account.get("mask")),
        "credit_limit": _money(balances.get("limit")),
        "current_balance": _money(balances.get("current")) or 0.0,
        "available_balance": _money(balances.get("available")),
        "purchase_apr": _purchase_apr(liability),
        "closing_day": _day_of_month((liability or {}).get("last_statement_issue_date")),
        "statement_day": _day_of_month((liability or {}).get("next_payment_due_date")),
    }


def build_transaction_payload(transaction: dict[str, Any]) -> dict[str, Any]:
    """Map one Plaid transaction to a `card_transactions` row.

    Plaid amounts are positive when money leaves the account (a purchase); we
    store them unchanged and document the sign in the schema.
    """
    legacy_categories = transaction.get("category") or []
    primary_category = (transaction.get("personal_finance_category") or {}).get("primary")
    return {
        "plaid_transaction_id": transaction["transaction_id"],
        "description": transaction.get("name"),
        "merchant_name": transaction.get("merchant_name"),
        "amount": _money(transaction.get("amount")) or 0.0,
        "category": primary_category or (legacy_categories[0] if legacy_categories else None),
        "authorized_date": transaction.get("authorized_date"),
        "posted_date": transaction.get("date"),
        "pending": bool(transaction.get("pending", False)),
        "iso_currency_code": transaction.get("iso_currency_code"),
    }


# --- sync orchestration -----------------------------------------------------


def _resolve_access_token(plaid: PlaidClient, request: PlaidSyncRequest) -> str:
    """Pick the access token: explicit -> env -> a fresh sandbox Item."""
    if request.access_token:
        return request.access_token
    if settings.plaid_access_token:
        return settings.plaid_access_token

    institution_id = request.institution_id or settings.plaid_sandbox_institution_id
    public_token = plaid.sandbox_public_token_create(institution_id)
    exchange = plaid.exchange_public_token(public_token)
    access_token = exchange.get("access_token")
    if not access_token:
        raise UpstreamServiceError("Plaid did not return an access token.")
    return access_token


def _credit_liabilities(plaid: PlaidClient, access_token: str) -> list[dict[str, Any]]:
    """Fetch credit liabilities; tolerate Items without the Liabilities product."""
    try:
        response = plaid.liabilities_get(access_token)
    except UpstreamServiceError as exc:
        logger.warning("Liabilities unavailable for this Item: %s", exc)
        return []
    return (response.get("liabilities") or {}).get("credit") or []


def _store_transactions(
    client: Client,
    user_id: str,
    card_id_by_account: dict[str, str],
    transactions: list[dict[str, Any]],
) -> int:
    """Upsert transactions grouped per card; skip accounts we did not store."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for transaction in transactions:
        card_id = card_id_by_account.get(transaction.get("account_id"))
        if card_id is None:
            continue
        grouped.setdefault(card_id, []).append(build_transaction_payload(transaction))

    total = 0
    for card_id, payloads in grouped.items():
        total += repository.upsert_transactions(
            client, user_id=user_id, card_id=card_id, payloads=payloads
        )
    return total


def sync_from_plaid(
    client: Client,
    *,
    user_id: str,
    plaid: PlaidClient,
    request: PlaidSyncRequest,
) -> PlaidSyncResponse:
    """Load one Plaid client's credit cards and transactions into the database."""
    access_token = _resolve_access_token(plaid, request)

    accounts_response = plaid.accounts_get(access_token)
    accounts = accounts_response.get("accounts") or []
    item = accounts_response.get("item") or {}
    item_id = item.get("item_id")
    if not item_id:
        raise UpstreamServiceError("Plaid did not return an item id for this account.")
    institution_name = item.get("institution_name")

    credit_accounts = [
        account for account in accounts if account.get("type") == CREDIT_ACCOUNT_TYPE
    ]
    if not credit_accounts:
        raise NotFoundError("The linked Plaid item has no credit card accounts.")

    liabilities = _credit_liabilities(plaid, access_token)
    liability_by_account = {
        liability.get("account_id"): liability for liability in liabilities
    }

    existing_item = repository.get_plaid_item(client, user_id=user_id, item_id=item_id)
    cursor = (existing_item or {}).get("transactions_cursor")

    item_row = repository.upsert_plaid_item(
        client,
        user_id=user_id,
        payload={
            "item_id": item_id,
            "access_token": access_token,
            "institution_id": item.get("institution_id"),
            "institution_name": institution_name,
        },
    )
    plaid_item_id = item_row.get("id")

    card_payloads = [
        {
            **build_card_payload(
                account,
                liability_by_account.get(account.get("account_id")),
                issuer=institution_name or "Unknown issuer",
            ),
            "plaid_item_id": plaid_item_id,
        }
        for account in credit_accounts
    ]
    card_rows = repository.upsert_cards(client, user_id=user_id, payloads=card_payloads)
    card_id_by_account = {
        row["plaid_account_id"]: row["id"]
        for row in card_rows
        if row.get("plaid_account_id") and row.get("id")
    }

    added, modified, removed, next_cursor = plaid.sync_all_transactions(
        access_token, cursor=cursor
    )

    added_count = _store_transactions(client, user_id, card_id_by_account, added)
    modified_count = _store_transactions(client, user_id, card_id_by_account, modified)

    removed_ids = [
        transaction["transaction_id"]
        for transaction in removed
        if transaction.get("transaction_id")
    ]
    removed_count = repository.delete_transactions_by_plaid_ids(
        client, user_id=user_id, plaid_transaction_ids=removed_ids
    )

    repository.update_plaid_item_cursor(
        client, user_id=user_id, item_id=item_id, cursor=next_cursor
    )

    return PlaidSyncResponse(
        item_id=item_id,
        institution_name=institution_name,
        cards_synced=len(card_rows),
        transactions_added=added_count,
        transactions_updated=modified_count,
        transactions_removed=removed_count,
        next_cursor=next_cursor,
    )
