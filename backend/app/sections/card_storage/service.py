"""Business logic for the Card Storage section.

TODO(card_storage owner):
  - `list_cards(client, user_id)` -> the caller's cards as `CreditCardRead`.
  - `create_card(client, user_id, payload)` -> created row; reject a
    `current_balance` above `credit_limit` with `ConflictError` or a validation error.
  - `update_card` / `delete_card` once the UI needs them.
"""

from supabase import Client

from app.sections.card_storage.schemas import CreditCardCreate, CreditCardRead


def list_cards(client: Client, *, user_id: str) -> list[CreditCardRead]:
    """Return every card stored for `user_id`."""
    raise NotImplementedError("TODO(card_storage): implement list_cards")


def create_card(client: Client, *, user_id: str, payload: CreditCardCreate) -> CreditCardRead:
    """Store a new card for `user_id` and return it."""
    raise NotImplementedError("TODO(card_storage): implement create_card")
