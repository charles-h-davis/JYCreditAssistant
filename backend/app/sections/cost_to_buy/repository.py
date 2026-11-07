"""Supabase access for the Cost to Buy section.

Table: `purchase_plans` (TODO: create the migration in Supabase, then replace the
`NotImplementedError` bodies below).

Every function takes an injected `Client` so tests can pass a fake and the router
owns the anon/service-role decision.
"""

from typing import Any

from supabase import Client

TABLE = "purchase_plans"


def list_purchase_plans(client: Client, *, user_id: str) -> list[dict[str, Any]]:
    """Return saved purchase plans belonging to `user_id`."""
    raise NotImplementedError(f"TODO(cost_to_buy): implement list_purchase_plans on '{TABLE}'")


def create_purchase_plan(
    client: Client, *, user_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Insert a purchase plan for `user_id` and return the created row."""
    raise NotImplementedError(f"TODO(cost_to_buy): implement create_purchase_plan on '{TABLE}'")
