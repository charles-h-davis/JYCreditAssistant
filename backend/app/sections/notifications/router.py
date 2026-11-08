"""HTTP routes for the Notifications section (mounted at /api/v1/notifications).

There is no JWT auth dependency yet, so user-scoped endpoints take an explicit
``user_id`` and the router injects the service-role Supabase client; every
repository query filters on that id.

Accepting a match (the ✓ in the UI) deletes the planned purchase through
``DELETE /api/v1/cost-to-buy/purchase-plans/{id}`` — the match disappears because
the plan does, so no dismissal row is needed for that path.

``TODO(notifications)``: replace the `user_id` parameters with the Supabase JWT
subject and `get_supabase_admin` with `get_supabase` once auth exists.
"""

from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.notifications import service
from app.sections.notifications.schemas import (
    DismissalCreate,
    DismissalRead,
    NotificationsFeed,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/ping", summary="Health check for the Notifications section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "notifications", "status": "ok"}


@router.get(
    "",
    response_model=NotificationsFeed,
    summary="Planned purchases that look like they have already been bought",
    responses={422: {"description": "Missing or empty user_id."}},
)
def get_notifications(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id whose plans and transactions are checked.",
    ),
    client: Client = Depends(get_supabase_admin),
) -> NotificationsFeed:
    """Return the bell badge count and the matches behind it, newest first."""
    return service.get_notifications(client, user_id=user_id)


@router.post(
    "/dismissals",
    response_model=DismissalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Stop notifying about one match (keep the planned purchase)",
    responses={422: {"description": "Missing user_id, plan_id or transaction_id."}},
)
def dismiss_match(
    payload: DismissalCreate,
    client: Client = Depends(get_supabase_admin),
) -> DismissalRead:
    """Remember the ✗ for one `(plan, transaction)` pair.

    Idempotent: dismissing the same pair again returns the stored row, so a
    double tap cannot fail. The planned purchase itself is untouched.
    """
    return service.dismiss(client, request=payload)
