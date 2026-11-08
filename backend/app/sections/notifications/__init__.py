"""Notifications section.

Turns "you already bought the thing you were planning to buy" into a notification:
the section watches the user's planned purchases and card transactions and reports
pairs whose amount and timing line up.

It owns one small table (`purchase_match_dismissals`) and only *reads* the tables
owned by `cost_to_buy` and `card_storage`, so accepting a match deletes the plan
through the Cost to Buy API rather than writing across sections.

Owner: _fill in_
"""

from app.sections.notifications.router import router

__all__ = ["router"]
