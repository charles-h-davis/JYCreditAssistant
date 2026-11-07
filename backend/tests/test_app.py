"""Application-level smoke tests: health probe and section auto-registration."""

from fastapi.testclient import TestClient

EXPECTED_SECTIONS = {
    "cost-to-buy",
    "credit-learning",
    "card-storage",
    "ai-assistant",
}


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_root_lists_docs(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_every_section_router_is_mounted(client: TestClient, api_prefix: str) -> None:
    """`app.sections` discovery must have mounted all four section routers."""
    for section in sorted(EXPECTED_SECTIONS):
        response = client.get(f"{api_prefix}/{section}/ping")

        assert response.status_code == 200, f"{section} router is not mounted"
        assert response.json() == {"section": section, "status": "ok"}


def test_openapi_schema_builds(client: TestClient) -> None:
    """Docs must stay valid — `/docs` is the contract the frontend codes against."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"]
