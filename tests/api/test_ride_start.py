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
async def test_ride_start_route_exists_returns_501(client: AsyncClient) -> None:
    resp = await client.post("/ride/start", json={"user_id": 1, "lon": 34.8, "lat": 32.1})
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_ride_start_rejects_string_user_id_strict(client: AsyncClient) -> None:
    resp = await client.post("/ride/start", json={"user_id": "1", "lon": 34.8, "lat": 32.1})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ride_start_requires_lon_lat_not_station_id(client: AsyncClient) -> None:
    # Must fail: lon/lat required, station_id forbidden
    resp = await client.post("/ride/start", json={"user_id": 1, "station_id": 10})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ride_start_extra_fields_forbidden(client: AsyncClient) -> None:
    resp = await client.post(
        "/ride/start",
        json={"user_id": 1, "lon": 34.8, "lat": 32.1, "station_id": 999},
    )
    assert resp.status_code == 400
