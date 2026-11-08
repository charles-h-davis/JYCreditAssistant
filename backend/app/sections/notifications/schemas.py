"""Request/response models for the Notifications section.

Names are snake_case throughout; money is GBP rounded to 2 decimals at the
boundary, and dates are plain dates (a card transaction has no time of day).
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PurchaseMatch(BaseModel):
    """A card transaction that looks like a planned purchase the user has now made."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Stable id for the pair: '<plan_id>:<transaction_id>'.")
    plan_id: str = Field(..., description="The planned purchase this transaction may have settled.")
    transaction_id: str = Field(..., description="The card transaction that matched the plan.")
    card_id: str = Field(..., description="The card both the plan and the transaction belong to.")
    product_name: str | None = Field(
        default=None, description="Product from the plan; null when the plan has no name."
    )
    amount: float = Field(
        ..., description="Matched amount in GBP — both sides agree to the penny."
    )
    merchant_name: str | None = Field(
        default=None,
        description="Merchant from the transaction, falling back to its raw description.",
    )
    transaction_date: date = Field(
        ..., description="Authorized date, falling back to the posted date."
    )
    planned_at: datetime = Field(..., description="When the planned purchase was created (UTC).")


class NotificationsFeed(BaseModel):
    """Everything the bell needs in one call."""

    count: int = Field(..., ge=0, description="Number of matches — the bell badge.")
    matches: list[PurchaseMatch] = Field(
        default_factory=list, description="The matches, newest transaction first."
    )


class DismissalCreate(BaseModel):
    """Stop notifying about one match (the ✗ action). The plan itself is kept."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the rows. Temporary until JWT auth.",
    )
    plan_id: str = Field(..., min_length=1, description="Plan side of the match being dismissed.")
    transaction_id: str = Field(
        ..., min_length=1, description="Transaction side of the match being dismissed."
    )


class DismissalRead(BaseModel):
    """A stored dismissal."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    plan_id: str
    transaction_id: str
    created_at: datetime | None = Field(
        default=None, description="When the match was dismissed (UTC)."
    )
