"""Startup / bootstrap smoketest.

Verifies that the FastAPI application factory completes without errors,
registers the expected routes, and serves basic requests correctly.
These tests are intentionally shallow: they prove the app *boots*, not
that every endpoint is correct (that belongs to the individual route test suites).
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

# NOTE: app/client fixtures come from tests/conftest.py now (dependency overridden)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def route_paths(app: FastAPI) -> set[str]:
    return {route.path for route in app.routes}


# ---------------------------------------------------------------------------
# Group 1 - app factory
# ---------------------------------------------------------------------------

class TestAppFactory:
    def test_returns_fastapi_instance(self, app: FastAPI) -> None:
        assert isinstance(app, FastAPI)

    def test_title(self, app: FastAPI) -> None:
        assert app.title == "Vehicle Sharing API"

    def test_version(self, app: FastAPI) -> None:
        assert app.version == "1.0.0"


# ---------------------------------------------------------------------------
# Group 2 - route registration
# ---------------------------------------------------------------------------

class TestRouteRegistration:
    def test_register_route_registered(self, app: FastAPI) -> None:
        assert "/register" in route_paths(app)

    # Keep this only if /health exists in your KAN-16 app
    def test_health_route_registered(self, app: FastAPI) -> None:
        assert "/health" in route_paths(app)


# ---------------------------------------------------------------------------
# Group 3 - basic HTTP behaviour
# ---------------------------------------------------------------------------

class TestHttpBehaviour:
    # Keep these only if /health exists in your KAN-16 app
    def test_health_returns_200(self, client: TestClient) -> None:
        assert client.get("/health").status_code == 200

    def test_health_returns_ok_body(self, client: TestClient) -> None:
        assert client.get("/health").json() == {"status": "ok"}

    def test_unknown_path_returns_404(self, client: TestClient) -> None:
        assert client.get("/no-such-route").status_code == 404

    def test_validation_error_returns_400_not_422(self, client: TestClient) -> None:
        """The custom RequestValidationError handler must downgrade 422 to 400."""
        response = client.post("/register", json={})
        assert response.status_code == 400
