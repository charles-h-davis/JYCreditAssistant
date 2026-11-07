"""Request/response models for the Card Storage section.

Field naming follows the product wording:

- ``closing_day``   — day of month the statement **closes** (statement day).
- ``statement_day`` — day of month the **payment is due** (due date).

No PAN, CVV or expiry date is modelled on purpose: this section stores balance
metadata, not payment credentials.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CreditCardCreate(BaseModel):
    """Metadata for a card the user wants to track by hand."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nickname": "Everyday card",
                "issuer": "Chase",
                "last_four": "4321",
                "credit_limit": 5000.0,
                "current_balance": 1875.4,
                "purchase_apr": 24.99,
                "closing_day": 12,
                "statement_day": 5,
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
    current_balance: float = Field(..., ge=0, description="Current debt (balance) in USD.")
    purchase_apr: float = Field(
        ...,
        ge=0,
        le=100,
        description="Purchase APR as a percent (24.99 means 24.99%).",
    )
    closing_day: int = Field(
        ..., ge=1, le=31, description="Statement closing day of month (1-31)."
    )
    statement_day: int = Field(
        ..., ge=1, le=31, description="Payment due day of month (1-31)."
    )
    is_secured: bool = Field(default=False, description="True for secured cards.")


class CreditCardRead(BaseModel):
    """A stored card as returned to the client.

    Unlike :class:`CreditCardCreate`, every financial field is optional: cards
    loaded from Plaid may not report a limit, available balance, APR or dates.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Row id (UUID).")
    user_id: str = Field(..., description="Owning user id (Supabase auth uid).")
    nickname: str = Field(..., description="User's label for the card.")
    issuer: str = Field(..., description="Card issuer, e.g. 'Chase'.")
    last_four: str = Field(..., description="Last four digits, for display only.")
    credit_limit: float | None = Field(
        default=None, description="Credit limit in USD, when the issuer reports one."
    )
    current_balance: float = Field(..., description="Current debt (balance) in USD.")
    available_balance: float | None = Field(
        default=None, description="Available credit in USD, when the issuer reports it."
    )
    purchase_apr: float | None = Field(
        default=None, description="Purchase APR as a percent (24.99 means 24.99%)."
    )
    closing_day: int | None = Field(
        default=None, description="Statement closing day of month (1-31)."
    )
    statement_day: int | None = Field(
        default=None, description="Payment due day of month (1-31)."
    )
    is_secured: bool = Field(default=False, description="True for secured cards.")
    plaid_item_id: str | None = Field(
        default=None, description="Owning Plaid Item row id, null for manual cards."
    )
    plaid_account_id: str | None = Field(
        default=None, description="Plaid account id, null for manual cards."
    )
    created_at: datetime | None = Field(default=None, description="Creation timestamp (UTC).")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp (UTC).")


class CardTransactionRead(BaseModel):
    """One card transaction loaded from Plaid."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Row id (UUID).")
    user_id: str = Field(..., description="Owning user id (Supabase auth uid).")
    card_id: str = Field(..., description="Owning credit card row id.")
    plaid_transaction_id: str = Field(..., description="Plaid transaction id (unique).")
    description: str | None = Field(default=None, description="Raw transaction description.")
    merchant_name: str | None = Field(default=None, description="Cleaned merchant name.")
    amount: float = Field(
        ...,
        description="Amount in USD. Plaid sign convention: positive means money left the account.",
    )
    category: str | None = Field(default=None, description="Primary spending category.")
    authorized_date: date | None = Field(default=None, description="Authorisation date.")
    posted_date: date | None = Field(default=None, description="Posted date.")
    pending: bool = Field(default=False, description="True while the transaction is pending.")
    iso_currency_code: str | None = Field(default=None, description="ISO 4217 currency code.")
    created_at: datetime | None = Field(default=None, description="Creation timestamp (UTC).")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp (UTC).")


class PlaidSyncRequest(BaseModel):
    """Ask the backend to load one client's Plaid item into the database."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "8d1c5c1e-6a8b-4f2e-9c3d-2b7f0a1e4d5c",
                "institution_id": "ins_56",
            }
        }
    )

    user_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Supabase auth user id (UUID) that will own the data. Temporary until the "
            "API has a JWT auth dependency."
        ),
    )
    institution_id: str | None = Field(
        default=None,
        description=(
            "Sandbox institution to link. Defaults to PLAID_SANDBOX_INSTITUTION_ID when "
            "no access token is supplied."
        ),
    )
    access_token: str | None = Field(
        default=None,
        description=(
            "Optional existing Plaid access token. Defaults to PLAID_ACCESS_TOKEN, and "
            "otherwise a fresh sandbox Item is created."
        ),
    )


class PlaidSyncResponse(BaseModel):
    """Summary of one Plaid -> database sync."""

    item_id: str = Field(..., description="Plaid Item id that was synced.")
    institution_name: str | None = Field(default=None, description="Institution name.")
    cards_synced: int = Field(..., description="Credit card rows written.")
    transactions_added: int = Field(..., description="Transactions inserted.")
    transactions_updated: int = Field(..., description="Transactions modified/updated.")
    transactions_removed: int = Field(..., description="Transactions deleted at the issuer.")
    next_cursor: str | None = Field(
        default=None, description="Plaid transactions cursor for the next incremental sync."
    )
