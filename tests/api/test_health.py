"""Health Check Endpoint Tests.

Tests for the health check endpoint to verify API availability and responsiveness.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app


@pytest.mark.anyio
async def test_health_ok():
    """Verify health endpoint returns 200 with ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
