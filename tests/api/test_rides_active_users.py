from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
       yield ac


@pytest.mark.asyncio
async def test_active_users_route_exists_returns_501(client: AsyncClient) -> None:
    resp = await client.get("/rides/active-users")
    assert resp.status_code == 501
