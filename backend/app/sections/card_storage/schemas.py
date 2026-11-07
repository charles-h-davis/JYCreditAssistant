"""Request/response models for the Card Storage section.

No PAN, CVV or expiry date is modelled on purpose: this section stores balance
metadata, not payment credentials.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreditCardCreate(BaseModel):
    """Metadata for a card the user wants to track."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nickname": "Everyday card",
                "issuer": "Chase",
                "last_four": "4321",
                "credit_limit": 5000.0,
                "current_balance": 1875.4,
                "apr": 24.99,
                "statement_day": 12,
                "due_day": 5,
            }
        }
    )

    nickname: str = Field(
        ..., min_length=1, max_length=60, description="User's label for the card."
    )
    issuer: str = Field(..., min_length=1, max_length=60, description="Card issuer, e.g. 'Chase'.")
    last_four: str = Field(
        ..., pattern=r"^\d{4}$", description="Last four digits, for display only."
    )
    credit_limit: float = Field(..., gt=0, description="Credit limit in USD.")
    current_balance: float = Field(..., ge=0, description="Current balance in USD.")
    apr: float = Field(
        ..., ge=0, le=100, description="Purchase APR as a percent (24.99 means 24.99%)."
    )
    statement_day: int = Field(..., ge=1, le=31, description="Statement closing day of month.")
    due_day: int = Field(..., ge=1, le=31, description="Payment due day of month.")
    is_secured: bool = Field(default=False, description="True for secured cards.")


class CreditCardRead(CreditCardCreate):
    """A stored card as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Row id (UUID).")
    user_id: str = Field(..., description="Owning user id (Supabase auth uid).")
    created_at: datetime | None = Field(default=None, description="Creation timestamp (UTC).")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp (UTC).")
