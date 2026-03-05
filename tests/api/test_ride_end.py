from collections.abc import AsyncIterator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.domain.exceptions import ConflictError, NotFoundError


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ride_end_happy_path_200(async_client: AsyncClient, fleet_manager_mock: Mock) -> None:
    fleet_manager_mock.end_ride.return_value = (7, 15)

    resp = await async_client.post("/ride/end", json={"ride_id": 10, "lon": 34.81, "lat": 32.11})
    assert resp.status_code == 200
    assert resp.json() == {"ride_id": 10, "end_station_id": 7, "payment_charged": 15}

    fleet_manager_mock.end_ride.assert_called_once_with(
        ride_id=10,
        location=(32.11, 34.81),
    )


@pytest.mark.asyncio
async def test_ride_end_maps_not_found_to_404(
    async_client: AsyncClient, fleet_manager_mock: Mock
) -> None:
    fleet_manager_mock.end_ride.side_effect = NotFoundError("Ride not found")

    resp = await async_client.post("/ride/end", json={"ride_id": 999, "lon": 34.81, "lat": 32.11})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ride_end_maps_conflict_to_409(
    async_client: AsyncClient, fleet_manager_mock: Mock
) -> None:
    fleet_manager_mock.end_ride.side_effect = ConflictError("Ride not active")

    resp = await async_client.post("/ride/end", json={"ride_id": 10, "lon": 34.81, "lat": 32.11})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_ride_end_rejects_string_ride_id_strict(async_client: AsyncClient) -> None:
    resp = await async_client.post("/ride/end", json={"ride_id": "10", "lon": 34.81, "lat": 32.11})
    # RequestValidationError is mapped to 400 by global exception handler
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ride_end_forbids_extra_fields(async_client: AsyncClient) -> None:
    resp = await async_client.post(
        "/ride/end",
        json={"ride_id": 10, "lon": 34.81, "lat": 32.11, "payment_charged_ils": 15},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_old_end_route_is_removed(async_client: AsyncClient) -> None:
    # Must be removed: POST /rides/{ride_id}/end
    resp = await async_client.post("/rides/123/end")
    assert resp.status_code == 404
