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
async def test_ride_end_route_exists_returns_501(client: AsyncClient) -> None:
    resp = await client.post("/ride/end", json={"ride_id": 10, "lon": 34.81, "lat": 32.11})
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_ride_end_rejects_string_ride_id_strict(client: AsyncClient) -> None:
    resp = await client.post("/ride/end", json={"ride_id": "10", "lon": 34.81, "lat": 32.11})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ride_end_forbids_extra_fields(client: AsyncClient) -> None:
    resp = await client.post(
        "/ride/end",
        json={"ride_id": 10, "lon": 34.81, "lat": 32.11, "payment_charged_ils": 15},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_old_end_route_is_removed(client: AsyncClient) -> None:
    # Must be removed: POST /rides/{ride_id}/end
    resp = await client.post("/rides/123/end")
    assert resp.status_code == 404
