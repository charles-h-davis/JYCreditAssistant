"""Supabase client factories.

Clients are built lazily and cached, so importing the app never performs network
I/O and the test suite runs without credentials configured.

Usage inside a section router::

    def list_cards(client: Client = Depends(get_supabase)) -> list[CreditCard]:
        return service.list_cards(client)
"""

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


class SupabaseNotConfiguredError(RuntimeError):
    """Raised when a Supabase client is requested without credentials set."""


def _build_client(url: str, key: str, *, credential_name: str) -> Client:
    if not url or not key:
        msg = (
            f"{credential_name} is not configured. Copy backend/.env.example to "
            "backend/.env and fill in SUPABASE_URL plus the Supabase keys."
        )
        raise SupabaseNotConfiguredError(msg)
    return create_client(url, key)


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Anon-key client.

    Respects Postgres Row Level Security, so it only sees rows the signed-in user
    is allowed to see. Prefer this one for user-scoped reads and writes.
    """
    return _build_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        credential_name="SUPABASE_ANON_KEY",
    )


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """Service-role client.

    Bypasses Row Level Security. Backend only: never send this key to the browser
    and never return data from it without an explicit ownership check.
    """
    return _build_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        credential_name="SUPABASE_SERVICE_ROLE_KEY",
    )
