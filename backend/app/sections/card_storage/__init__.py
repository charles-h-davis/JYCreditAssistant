"""Card Storage section.

Stores the user's credit cards (issuer, limit, balance, APR, due dates) as the
source of truth every other section can plan against.

Security note: we never store or accept a full card number, CVV or expiry —
`last_four` is display-only metadata. Anything that looks like a PAN is a bug.

Owner: _fill in_
"""

from app.sections.card_storage.router import router

__all__ = ["router"]
