"""HTTP routes for the Cost to Buy section (mounted at /api/v1/cost-to-buy).

The calculator endpoints (`/estimate`, `/purchase-impact`) are pure and stateless.
The persistence endpoints take an explicit ``user_id`` and inject the service-role
Supabase client (there is no JWT auth yet); ownership is enforced by the
repository's ``user_id`` filters. ``TODO(cost_to_buy)``: replace ``user_id`` with
the JWT subject and switch to ``get_supabase`` once auth exists.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.cost_to_buy import service
from app.sections.cost_to_buy.gemini_client import GeminiClient, get_gemini_client
from app.sections.cost_to_buy.schemas import (
    ExtractResponse,
    MonthlyPaymentRead,
    MonthlyPaymentUpsert,
    PurchaseCostRequest,
    PurchaseCostResponse,
    PurchaseImpactRequest,
    PurchaseImpactResponse,
    PurchasePlanCreate,
    PurchasePlanRead,
)

router = APIRouter(prefix="/cost-to-buy", tags=["Cost to Buy"])

#: Image types Gemini accepts that we also accept for extraction.
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}
#: Upper bound on the uploaded image so one request can't exhaust memory.
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.get("/ping", summary="Health check for the Cost to Buy section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "cost-to-buy", "status": "ok"}


@router.post(
    "/estimate",
    response_model=PurchaseCostResponse,
    summary="Estimate the true cost of a purchase financed on a credit card",
    responses={
        422: {"description": "Invalid amount/APR, or a payment that can't cover interest."}
    },
)
def estimate_purchase_cost(payload: PurchaseCostRequest) -> PurchaseCostResponse:
    """Return total interest, months to payoff and payoff date for one purchase."""
    try:
        return service.estimate_purchase_cost(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/purchase-impact",
    response_model=PurchaseImpactResponse,
    summary="Show the extra cost of a new purchase on an existing card balance",
    responses={
        422: {"description": "Invalid payload or a payment that can't cover interest."}
    },
)
def purchase_impact(payload: PurchaseImpactRequest) -> PurchaseImpactResponse:
    """Compare the current plan with the same plan plus the new purchase."""
    try:
        return service.purchase_impact(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extract a product name and price from a price-tag or product image",
    responses={
        413: {"description": "Image is too large."},
        415: {"description": "Unsupported image type."},
        422: {"description": "Missing image."},
        503: {"description": "Gemini is not configured (see backend/.env)."},
    },
)
def extract(
    file: Annotated[
        UploadFile, File(description="Image of a price tag, product or receipt line.")
    ],
    gemini: GeminiClient = Depends(get_gemini_client),
) -> ExtractResponse:
    """Read a product name and price out of an uploaded image using Gemini."""
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type: {content_type or 'unknown'}.",
        )

    image_bytes = file.file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large (max 10 MB).")

    return service.extract_product(
        gemini, image_bytes=image_bytes, mime_type=content_type
    )


@router.get(
    "/purchase-plans",
    response_model=list[PurchasePlanRead],
    summary="List a user's confirmed purchase plans",
    responses={422: {"description": "Missing or empty user_id."}},
)
def list_purchase_plans(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> list[PurchasePlanRead]:
    """Return every purchase plan stored for `user_id`, newest first."""
    return service.list_purchase_plans(client, user_id=user_id)


@router.post(
    "/purchase-plans",
    response_model=PurchasePlanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm a purchase: store the plan and set the new monthly payment",
    responses={422: {"description": "Invalid plan payload or missing user_id."}},
)
def create_purchase_plan(
    payload: PurchasePlanCreate,
    client: Client = Depends(get_supabase_admin),
) -> PurchasePlanRead:
    """Store a confirmed purchase and make its payment the current monthly payment."""
    return service.record_purchase_plan(client, user_id=payload.user_id, payload=payload)


@router.get(
    "/monthly-payment",
    response_model=MonthlyPaymentRead,
    summary="Get the stored monthly payment for a card",
    responses={
        404: {"description": "No monthly payment stored for this card yet."},
        422: {"description": "Missing user_id or card_id."},
    },
)
def get_monthly_payment(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id (temporary until JWT auth).",
    ),
    card_id: str = Query(..., min_length=1, description="Card the payment belongs to."),
    client: Client = Depends(get_supabase_admin),
) -> MonthlyPaymentRead:
    """Return the card's current monthly payment, or 404 if none is stored."""
    return service.get_monthly_payment(client, user_id=user_id, card_id=card_id)


@router.put(
    "/monthly-payment",
    response_model=MonthlyPaymentRead,
    summary="Set the current monthly payment for a card",
    responses={422: {"description": "Invalid payload or missing user_id."}},
)
def set_monthly_payment(
    payload: MonthlyPaymentUpsert,
    client: Client = Depends(get_supabase_admin),
) -> MonthlyPaymentRead:
    """Store the card's current monthly payment (initial entry or an update)."""
    return service.set_monthly_payment(
        client,
        user_id=payload.user_id,
        card_id=payload.card_id,
        monthly_payment=payload.monthly_payment,
    )
