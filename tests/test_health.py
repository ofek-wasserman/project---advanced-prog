"""Health Check Endpoint Tests.

Tests for the health check endpoint to verify API availability and responsiveness.
"""

import pytest
from httpx import AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_health_ok():
    """Verify health endpoint returns 200 with ok status."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
