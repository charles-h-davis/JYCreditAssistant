"""Domain errors and their HTTP representation.

Sections raise these from their service layer instead of `HTTPException`, so the
same error shape is returned by every endpoint::

    {"error": {"code": "not_found", "message": "..."}}

Database failures from ``postgrest`` are mapped here too. That matters for more
than tidiness: an unhandled exception is turned into a 500 by Starlette *outside*
the CORS middleware, so the browser sees an opaque "blocked by CORS policy" error
instead of the real problem. Handling them inside the exception middleware keeps
the CORS headers (and the message readable).
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for expected application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        super().__init__(self.message)


class NotFoundError(AppError):
    """A requested resource does not exist (or is not visible to this user)."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "The requested resource was not found."


class ConflictError(AppError):
    """The request conflicts with the current state of the resource."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "The request conflicts with the current state of the resource."


class UpstreamServiceError(AppError):
    """Supabase or an LLM provider failed in a way we cannot recover from."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "upstream_error"
    message = "An upstream service (database or model provider) failed."


class DatabaseNotReadyError(AppError):
    """A table the endpoint needs has not been created yet (PGRST205)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "database_not_ready"
    message = (
        "This feature's database tables haven't been created yet. Run the matching "
        "schema.sql from backend/app/sections/ in the Supabase SQL editor."
    )


def _postgrest_code(exc: Exception) -> str | None:
    """Best-effort read of PostgREST's error code from an ``APIError``."""
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code
    args = getattr(exc, "args", ())
    if args and isinstance(args[0], dict):
        candidate = args[0].get("code")
        if isinstance(candidate, str):
            return candidate
    return None


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the `AppError` handler so all sections return the same error JSON."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    try:
        from postgrest.exceptions import APIError as PostgrestAPIError
    except ImportError:  # pragma: no cover - postgrest ships with supabase-py
        return

    @app.exception_handler(PostgrestAPIError)
    async def _handle_postgrest_error(
        _request: Request, exc: PostgrestAPIError
    ) -> JSONResponse:
        if _postgrest_code(exc) == "PGRST205":
            return JSONResponse(
                status_code=DatabaseNotReadyError.status_code,
                content={
                    "error": {
                        "code": DatabaseNotReadyError.code,
                        "message": DatabaseNotReadyError.message,
                    }
                },
            )
        return JSONResponse(
            status_code=UpstreamServiceError.status_code,
            content={
                "error": {
                    "code": UpstreamServiceError.code,
                    "message": "The database rejected the request.",
                }
            },
        )

