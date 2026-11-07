"""HTTP routes for the Card Storage section (mounted at /api/v1/card-storage).

The API has no auth dependency yet, so every endpoint takes an explicit ``user_id``
and the router injects the service-role Supabase client; ownership is enforced by
the repository's `user_id` filters.

``TODO(card_storage)``: replace the `user_id` parameter with the Supabase JWT
subject and `get_supabase_admin` with `get_supabase` once auth exists.
"""

from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.card_storage import service
from app.sections.card_storage.plaid_client import PlaidClient, get_plaid_client
from app.sections.card_storage.schemas import (
    CardTransactionRead,
    CreditCardCreate,
    CreditCardRead,
    PlaidSyncRequest,
    PlaidSyncResponse,
)

router = APIRouter(prefix="/card-storage", tags=["Card Storage"])


@router.get("/ping", summary="Health check for the Card Storage section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "card-storage", "status": "ok"}


@router.get(
    "/cards",
    response_model=list[CreditCardRead],
    summary="List a user's stored cards",
    responses={422: {"description": "Missing or empty user_id."}},
)
def list_cards(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the data (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> list[CreditCardRead]:
    """Return every card stored for `user_id`, oldest first."""
    return service.list_cards(client, user_id=user_id)


@router.post(
    "/cards",
    response_model=CreditCardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Store a card by hand",
    responses={
        409: {"description": "current_balance is above credit_limit."},
        422: {"description": "Invalid card payload or missing user_id."},
    },
)
def create_card(
    payload: CreditCardCreate,
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that will own the card (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> CreditCardRead:
    """Persist a manually entered card (metadata only — never a full card number)."""
    return service.create_card(client, user_id=user_id, payload=payload)


@router.get(
    "/cards/{card_id}/transactions",
    response_model=list[CardTransactionRead],
    summary="List a card's stored transaction history",
    responses={
        404: {"description": "Card not found for this user."},
        422: {"description": "Missing or empty user_id."},
    },
)
def list_card_transactions(
    card_id: str,
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the data (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> list[CardTransactionRead]:
    """Return the transaction history loaded from Plaid for one of the user's cards."""
    return service.list_card_transactions(client, user_id=user_id, card_id=card_id)


@router.post(
    "/plaid/sync",
    response_model=PlaidSyncResponse,
    summary="Load a Plaid sandbox client's cards and transactions into the database",
    responses={
        404: {"description": "The Plaid item has no credit card accounts."},
        422: {"description": "Invalid sync payload."},
        502: {"description": "Plaid rejected the request or returned bad data."},
        503: {"description": "Plaid credentials are not configured (see backend/.env)."},
    },
)
def sync_from_plaid(
    payload: PlaidSyncRequest,
    client: Client = Depends(get_supabase_admin),
    plaid: PlaidClient = Depends(get_plaid_client),
) -> PlaidSyncResponse:
    """Create (or reuse) a Plaid Item, then upsert its cards and transaction history.

    When `access_token` is omitted the endpoint uses `PLAID_ACCESS_TOKEN` from the
    environment, or creates a fresh sandbox Item via `/sandbox/public_token/create`
    and exchanges it for an access token. Re-running the sync is idempotent and
    incremental thanks to the stored transactions cursor.
    """
    return service.sync_from_plaid(
        client, user_id=payload.user_id, plaid=plaid, request=payload
    )
