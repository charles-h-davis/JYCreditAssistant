"""HTTP routes for the Card Storage section (mounted at /api/v1/card-storage).

These endpoints are stubs, so they deliberately do not inject the Supabase client yet:
FastAPI resolves `Depends(...)` before the handler body runs, and the test suite has to
stay green without credentials.
"""

from fastapi import APIRouter, HTTPException, status

from app.sections.card_storage.schemas import CreditCardCreate, CreditCardRead

router = APIRouter(prefix="/card-storage", tags=["Card Storage"])

NOT_IMPLEMENTED = {
    status.HTTP_501_NOT_IMPLEMENTED: {"description": "Not implemented yet (scaffold stub)."}
}


@router.get("/ping", summary="Health check for the Card Storage section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "card-storage", "status": "ok"}


@router.get(
    "/cards",
    response_model=list[CreditCardRead],
    summary="List the signed-in user's stored cards",
    responses=NOT_IMPLEMENTED,
)
def list_cards() -> list[CreditCardRead]:
    """Return the caller's cards.

    TODO(card_storage owner): add `client: Client = Depends(get_supabase)` and delegate
    to `service.list_cards(client, user_id=...)` once auth supplies the user id.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="card_storage.list_cards is not implemented yet.",
    )


@router.post(
    "/cards",
    response_model=CreditCardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Store a new card for the signed-in user",
    responses={
        422: {"description": "Invalid card payload."},
        **NOT_IMPLEMENTED,
    },
)
def create_card(payload: CreditCardCreate) -> CreditCardRead:
    """Persist a card (metadata only — never a full card number).

    TODO(card_storage owner): add `client: Client = Depends(get_supabase)` and delegate
    to `service.create_card(client, user_id=..., payload=payload)`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="card_storage.create_card is not implemented yet.",
    )
