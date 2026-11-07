"""Request/response models for the Cost to Buy section.

Unit conventions (see `.clinerules/20-backend-conventions.md`): money is USD and
APR is a percentage — `24.99` means 24.99%, not 0.2499.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PurchaseCostRequest(BaseModel):
    """Inputs for estimating the real cost of a purchase financed on a card."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"purchase_amount": 1200.0, "apr": 24.99, "monthly_payment": 150.0}
        }
    )

    purchase_amount: float = Field(..., gt=0, description="Purchase price in USD.")
    apr: float = Field(
        ...,
        ge=0,
        le=100,
        description="Annual percentage rate as a percent (24.99 means 24.99%).",
    )
    monthly_payment: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Planned monthly payment in USD. When omitted, the issuer's minimum "
            "payment calculation should be used."
        ),
    )


class PurchaseCostResponse(BaseModel):
    """The true cost of the purchase once interest is accounted for."""

    purchase_amount: float = Field(..., description="Purchase price in USD.")
    apr: float = Field(..., description="APR used for the estimate, as a percent.")
    monthly_payment: float = Field(..., description="Monthly payment used, in USD.")
    months_to_payoff: int = Field(..., ge=0, description="Number of monthly payments needed.")
    total_interest: float = Field(
        ..., ge=0, description="Interest paid over the life of the balance."
    )
    total_paid: float = Field(..., ge=0, description="Principal plus interest, in USD.")
    payoff_date: date | None = Field(
        default=None,
        description="Projected payoff date, if a start date was supplied with the request.",
    )
