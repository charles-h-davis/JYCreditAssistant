"""Shared pytest fixtures.

The suite must pass without Supabase credentials: only `/ping`, `/health` and
validation paths are exercised at this stage.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """A TestClient bound to the real app (lifespan-aware)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def api_prefix() -> str:
    """The API prefix every section router is mounted under, e.g. `/api/v1`."""
    return settings.api_prefix
