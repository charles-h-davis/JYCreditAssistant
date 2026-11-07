"""HTTP routes for the Cost to Buy section (mounted at /api/v1/cost-to-buy)."""

from fastapi import APIRouter, HTTPException, status

from app.sections.cost_to_buy.schemas import PurchaseCostRequest, PurchaseCostResponse

router = APIRouter(prefix="/cost-to-buy", tags=["Cost to Buy"])


@router.get("/ping", summary="Health check for the Cost to Buy section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "cost-to-buy", "status": "ok"}


@router.post(
    "/estimate",
    response_model=PurchaseCostResponse,
    summary="Estimate the true cost of a purchase financed on a credit card",
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Not implemented yet (scaffold stub)."},
    },
)
def estimate_purchase_cost(payload: PurchaseCostRequest) -> PurchaseCostResponse:
    """Return total interest, months to payoff and payoff date for a purchase.

    TODO(cost_to_buy owner): delegate to `app.sections.cost_to_buy.service`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="cost_to_buy.estimate is not implemented yet.",
    )
