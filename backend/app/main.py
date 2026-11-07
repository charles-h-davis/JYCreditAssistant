"""FastAPI application factory for the JY Credit Assistant API.

Lead-owned: section owners do not need to edit this file. Section routers are
discovered from `app.sections` and mounted automatically under the API prefix.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.sections import get_section_routers

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Build the API, mounting every section router under the API prefix."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend for JY Credit Assistant — cost-to-buy planning, credit learning, "
            "card storage and AI credit guidance."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env, "version": settings.app_version}

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"name": settings.app_name, "docs": "/docs", "health": "/health"}

    routers = get_section_routers()
    for router in routers:
        app.include_router(router, prefix=settings.api_prefix)

    logger.info(
        "Mounted %d section router(s) under %s: %s",
        len(routers),
        settings.api_prefix,
        ", ".join(tag for router in routers for tag in router.tags) or "none",
    )
    return app


app = create_app()
