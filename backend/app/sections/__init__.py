"""Section registry.

Every child package of ``app.sections`` that exposes an ``APIRouter`` named
``router`` is mounted automatically by :func:`app.main.create_app` under the
configured API prefix. Adding a section therefore never requires editing the
shared application module.

To add a section, create ``app/sections/<section_name>/__init__.py`` containing::

    from app.sections.<section_name>.router import router

    __all__ = ["router"]
"""

import importlib
import logging
import pkgutil
from collections.abc import Iterator
from types import ModuleType

from fastapi import APIRouter

logger = logging.getLogger(__name__)


def iter_section_modules() -> Iterator[ModuleType]:
    """Import and yield every section sub-package of this module."""
    for module_info in pkgutil.iter_modules(__path__):
        if not module_info.ispkg:
            continue
        yield importlib.import_module(f"{__name__}.{module_info.name}")


def get_section_routers() -> list[APIRouter]:
    """Collect the ``router`` exposed by each section package."""
    routers: list[APIRouter] = []
    for module in iter_section_modules():
        router = getattr(module, "router", None)
        if not isinstance(router, APIRouter):
            logger.warning(
                "Section package %s does not expose an APIRouter named 'router'",
                module.__name__,
            )
            continue
        routers.append(router)
        logger.debug("Discovered section router: %s", module.__name__)
    return routers
