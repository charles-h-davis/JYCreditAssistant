"""Thin synchronous client for the Plaid REST API.

The section talks to Plaid over plain HTTPS (`httpx`) instead of adding the
`plaid-python` dependency. Calls are synchronous so routes stay plain `def` and
FastAPI runs them in its threadpool — never block the event loop with these.

Credentials come from `app.core.config.settings` (loaded from `backend/.env`).
No network I/O happens at import time.
"""

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AppError, UpstreamServiceError

logger = logging.getLogger(__name__)

#: Products requested when a sandbox Item is created. Both are needed for the
#: statements/APR fields and the transaction history we store.
SANDBOX_PRODUCTS = ["transactions", "liabilities"]

REQUEST_TIMEOUT_SECONDS = 30.0


class PlaidNotConfiguredError(AppError):
    """Raised when Plaid credentials are missing from the environment."""

    status_code = 503
    code = "plaid_not_configured"
    message = (
        "Plaid is not configured. Set PLAID_CLIENT_ID and PLAID_SECRET in backend/.env "
        "(see .env.example)."
    )


class PlaidClient:
    """Minimal Plaid API wrapper (only the endpoints this section needs)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        client_id: str | None = None,
        secret: str | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = (base_url or settings.plaid_base_url).rstrip("/")
        self.client_id = client_id if client_id is not None else settings.plaid_client_id
        self.secret = secret if secret is not None else settings.plaid_secret
        self.timeout = timeout

    # --- internals ---------------------------------------------------------

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"client_id": self.client_id, "secret": self.secret, **payload}
        try:
            with httpx.Client(timeout=self.timeout) as http_client:
                response = http_client.post(f"{self.base_url}{path}", json=body)
        except httpx.HTTPError as exc:
            raise UpstreamServiceError(f"Plaid request to {path} failed: {exc}") from exc

        if response.status_code >= 400:
            try:
                error = response.json()
            except ValueError:
                error = {}
            error_code = error.get("error_code") or f"HTTP_{response.status_code}"
            error_message = error.get("error_message") or response.text[:200]
            logger.warning("Plaid %s failed: %s (%s)", path, error_code, error_message)
            raise UpstreamServiceError(f"Plaid {error_code}: {error_message}")

        return response.json()

    # --- endpoints ---------------------------------------------------------

    def sandbox_public_token_create(
        self, institution_id: str, products: list[str] | None = None
    ) -> str:
        """Create a Sandbox Item without Link and return its public token."""
        response = self._post(
            "/sandbox/public_token/create",
            {
                "institution_id": institution_id,
                "initial_products": products or SANDBOX_PRODUCTS,
            },
        )
        public_token = response.get("public_token")
        if not public_token:
            raise UpstreamServiceError("Plaid did not return a sandbox public token.")
        return public_token

    def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        """Exchange a public token for the Item's long-lived access token."""
        return self._post("/item/public_token/exchange", {"public_token": public_token})

    def accounts_get(self, access_token: str) -> dict[str, Any]:
        """Fetch the Item's accounts and balances."""
        return self._post("/accounts/get", {"access_token": access_token})

    def liabilities_get(self, access_token: str) -> dict[str, Any]:
        """Fetch credit/loan liabilities (APRs, statement and due dates)."""
        return self._post("/liabilities/get", {"access_token": access_token})

    def transactions_sync(
        self, access_token: str, *, cursor: str | None = None, count: int = 250
    ) -> dict[str, Any]:
        """Fetch one page of transaction updates."""
        payload: dict[str, Any] = {"access_token": access_token, "count": count}
        if cursor:
            payload["cursor"] = cursor
        return self._post("/transactions/sync", payload)

    def sync_all_transactions(
        self, access_token: str, *, cursor: str | None = None, count: int = 250
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str | None]:
        """Page through `/transactions/sync` and return all changes in one go."""
        added: list[dict[str, Any]] = []
        modified: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        next_cursor = cursor

        while True:
            page = self.transactions_sync(access_token, cursor=next_cursor, count=count)
            added.extend(page.get("added") or [])
            modified.extend(page.get("modified") or [])
            removed.extend(page.get("removed") or [])
            next_cursor = page.get("next_cursor") or next_cursor
            if not page.get("has_more"):
                break

        return added, modified, removed, next_cursor


def get_plaid_client() -> PlaidClient:
    """FastAPI dependency: a configured Plaid client, or 503 when keys are missing."""
    if not settings.plaid_client_id or not settings.plaid_secret:
        raise PlaidNotConfiguredError()
    return PlaidClient()
