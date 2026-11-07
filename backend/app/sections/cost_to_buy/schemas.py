"""Request/response models for the Cost to Buy section.

Unit conventions (see ``.clinerules/20-backend-conventions.md``): money is GBP and
APR is a percentage — ``24.99`` means 24.99%, not 0.2499.

Card fields mirror the ``card_storage`` schema: ``current_balance``,
``purchase_apr``, ``closing_day`` (the statement-close day, when interest is
assessed) and ``statement_day`` (the payment-due day, which anchors the payoff
date).
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_CURRENCY = "GBP"


class PurchaseCostRequest(BaseModel):
    """Inputs for estimating the real cost of one purchase financed on a card."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "purchase_amount": 1200.0,
                "purchase_apr": 24.99,
                "monthly_payment": 150.0,
                "closing_day": 12,
                "statement_day": 5,
            }
        }
    )

    purchase_amount: float = Field(..., gt=0, description="Purchase price in GBP.")
    purchase_apr: float = Field(
        ..., ge=0, le=100, description="Purchase APR as a percent (24.99 = 24.99%)."
    )
    monthly_payment: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Planned monthly payment in GBP. When omitted, the payment that clears "
            "the purchase in 24 months is used."
        ),
    )
    closing_day: int | None = Field(
        default=None,
        ge=1,
        le=31,
        description="Statement-close day of month; interest is assessed on this day.",
    )
    statement_day: int | None = Field(
        default=None,
        ge=1,
        le=31,
        description="Payment-due day of month; anchors the payoff date.",
    )
    start_date: date | None = Field(
        default=None,
        description="Reference date for the schedule (defaults to today).",
    )


class PurchaseCostResponse(BaseModel):
    """The true cost of one purchase once interest is accounted for."""

    currency: str = Field(default=DEFAULT_CURRENCY, description="Currency code (GBP).")
    purchase_amount: float = Field(..., description="Purchase price in GBP.")
    purchase_apr: float = Field(..., description="APR used for the estimate, as a percent.")
    monthly_payment: float = Field(..., description="Monthly payment used, in GBP.")
    months_to_payoff: int = Field(
        ..., ge=0, description="Number of monthly payments needed."
    )
    total_interest: float = Field(
        ..., ge=0, description="Interest paid over the life of the balance."
    )
    total_paid: float = Field(..., ge=0, description="Principal plus interest, in GBP.")
    payoff_date: date | None = Field(
        default=None,
        description="Projected payoff date, when closing/statement days are supplied.",
    )


class PayoffSummary(BaseModel):
    """Outcome of amortising one balance at a fixed monthly payment."""

    months_to_payoff: int = Field(
        ..., ge=0, description="Number of monthly payments needed."
    )
    total_interest: float = Field(..., ge=0, description="Interest paid, in GBP.")
    total_paid: float = Field(..., ge=0, description="Principal plus interest, in GBP.")
    payoff_date: date | None = Field(
        default=None, description="Projected final-payment date."
    )


class PaymentScenario(BaseModel):
    """One 'what if I paid this much each month' option."""

    monthly_payment: float = Field(
        ..., gt=0, description="Monthly payment for this scenario, in GBP."
    )
    months_to_payoff: int = Field(
        ..., ge=0, description="Payments needed at this amount."
    )
    total_interest: float = Field(
        ..., ge=0, description="Interest paid at this amount, in GBP."
    )
    extra_total_paid: float = Field(
        ..., description="Extra total paid vs. the current plan, in GBP."
    )
    payoff_date: date | None = Field(
        default=None, description="Projected payoff date."
    )


class PurchaseImpactRequest(BaseModel):
    """The extra cost of a new purchase on an existing card balance."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_balance": 1800.0,
                "purchase_apr": 24.99,
                "purchase_amount": 120.0,
                "current_monthly_payment": 150.0,
                "closing_day": 12,
                "statement_day": 5,
            }
        }
    )

    current_balance: float = Field(
        ..., ge=0, description="Card balance before the purchase, in GBP."
    )
    purchase_apr: float = Field(
        ..., ge=0, le=100, description="Purchase APR as a percent."
    )
    purchase_amount: float = Field(..., gt=0, description="Price of the new item, in GBP.")
    current_monthly_payment: float = Field(
        ..., gt=0, description="The user's current monthly repayment, in GBP."
    )
    closing_day: int = Field(
        ..., ge=1, le=31, description="Statement-close day; interest is assessed here."
    )
    statement_day: int = Field(
        ..., ge=1, le=31, description="Payment-due day; anchors the payoff date."
    )
    payment_scenarios: list[float] | None = Field(
        default=None,
        description="Extra monthly payments to simulate. Defaults to a sensible ladder.",
    )
    start_date: date | None = Field(
        default=None, description="Reference date (defaults to today)."
    )
    currency: str = Field(default=DEFAULT_CURRENCY, description="Currency code (GBP).")

    @model_validator(mode="after")
    def _payment_must_cover_interest(self) -> "PurchaseImpactRequest":
        if self.purchase_apr > 0:
            monthly_rate = (self.purchase_apr / 100) / 12
            monthly_interest = (self.current_balance + self.purchase_amount) * monthly_rate
            if self.current_monthly_payment <= monthly_interest:
                raise ValueError(
                    "current_monthly_payment must exceed the monthly interest on the "
                    "balance; otherwise the debt never gets repaid."
                )
        return self


class PurchaseImpactResponse(BaseModel):
    """How much extra the new purchase really costs at the current repayment."""

    currency: str = Field(default=DEFAULT_CURRENCY, description="Currency code (GBP).")
    current_balance: float = Field(
        ..., description="Card balance before the purchase, in GBP."
    )
    purchase_apr: float = Field(..., description="APR used, as a percent.")
    purchase_amount: float = Field(..., description="Price of the new item, in GBP.")
    current_monthly_payment: float = Field(
        ..., description="The user's current monthly repayment, in GBP."
    )
    baseline: PayoffSummary = Field(
        ..., description="Plan with the existing balance only."
    )
    with_purchase: PayoffSummary = Field(
        ..., description="Plan with the new purchase added."
    )
    extra_total_paid: float = Field(
        ...,
        description=(
            "Extra total currency paid because of the purchase (headline number), in GBP."
        ),
    )
    extra_interest: float = Field(
        ..., description="Extra interest caused by the purchase, in GBP."
    )
    extra_months: int = Field(
        ..., ge=0, description="Extra monthly payments needed because of the purchase."
    )
    scenarios: list[PaymentScenario] = Field(
        default_factory=list, description="Payoff for adjusted monthly payments."
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Modelling notes shown under the numbers."
    )


class ExtractResponse(BaseModel):
    """Product name and price read from a price-tag / product image."""

    product_name: str | None = Field(
        default=None, description="Extracted product name, if any."
    )
    price: float | None = Field(
        default=None, description="Extracted price in the image's currency, if legible."
    )
    currency: str | None = Field(
        default=None, description="ISO 4217 currency code, if detectable."
    )
    raw_text: str | None = Field(
        default=None, description="Raw text the price/name was read from."
    )
    confidence: float | None = Field(
        default=None, ge=0, le=1, description="Model confidence, 0-1."
    )
    model: str | None = Field(
        default=None, description="Model that produced the extraction."
    )


class PurchasePlanCreate(BaseModel):
    """Confirm a purchase: store it and set the card's new monthly payment."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "8d1c5c1e-6a8b-4f2e-9c3d-2b7f0a1e4d5c",
                "card_id": "b0e1c2d3-4567-89ab-cdef-0123456789ab",
                "product_name": "Running shoes",
                "purchase_amount": 120.0,
                "monthly_payment": 175.0,
            }
        }
    )

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id (temporary until JWT auth).",
    )
    card_id: str = Field(..., min_length=1, description="Card the purchase goes on.")
    product_name: str | None = Field(
        default=None, max_length=200, description="Item name, if known."
    )
    purchase_amount: float = Field(..., gt=0, description="Price of the item, in GBP.")
    currency: str = Field(default=DEFAULT_CURRENCY, description="Currency code (GBP).")
    monthly_payment: float = Field(
        ..., gt=0, description="New monthly repayment to store, in GBP."
    )
    months_to_payoff: int | None = Field(
        default=None, ge=0, description="Optional snapshot of the estimate."
    )
    total_interest: float | None = Field(
        default=None, ge=0, description="Optional snapshot of the estimate."
    )


class PurchasePlanRead(BaseModel):
    """A stored purchase plan."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Row id (UUID).")
    user_id: str = Field(..., description="Owning user id (Supabase auth uid).")
    card_id: str = Field(..., description="Card the purchase is on.")
    product_name: str | None = Field(default=None, description="Item name, if known.")
    purchase_amount: float = Field(..., description="Price of the item, in GBP.")
    currency: str = Field(default=DEFAULT_CURRENCY, description="Currency code (GBP).")
    monthly_payment: float = Field(
        ..., description="Monthly repayment stored with the plan, in GBP."
    )
    months_to_payoff: int | None = Field(
        default=None, description="Snapshot of the estimate."
    )
    total_interest: float | None = Field(
        default=None, description="Snapshot of the estimate."
    )
    created_at: datetime | None = Field(
        default=None, description="Creation timestamp (UTC)."
    )


class MonthlyPaymentUpsert(BaseModel):
    """Set the current monthly payment for one card."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id (temporary until JWT auth).",
    )
    card_id: str = Field(..., min_length=1, description="Card the payment belongs to.")
    monthly_payment: float = Field(
        ..., gt=0, description="Current monthly repayment, in GBP."
    )


class MonthlyPaymentRead(BaseModel):
    """The stored monthly payment for one card."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(..., description="Owning user id (Supabase auth uid).")
    card_id: str = Field(..., description="Card the payment belongs to.")
    monthly_payment: float = Field(
        ..., description="Current monthly repayment, in GBP."
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp (UTC)."
    )
