import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.anyio
async def test_register_missing_body_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/users/register", json={})  # missing payment_token
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_start_ride_wrong_types_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/rides/start",
            json={"user_id": "not-an-int", "station_id": 1},
        )
    assert resp.status_code == 404
