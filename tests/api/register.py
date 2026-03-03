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
async def test_register_route_exists_returns_501(client: AsyncClient) -> None:
    resp = await client.post("/register", json={"payment_token": "tok_123"})
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_register_strict_types_rejects_non_string_token(client: AsyncClient) -> None:
    # strict=True => int is NOT coerced to str
    resp = await client.post("/register", json={"payment_token": 123})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_extra_fields_forbidden(client: AsyncClient) -> None:
    # extra="forbid"
    resp = await client.post("/register", json={"payment_token": "tok", "extra": "nope"})
    assert resp.status_code == 400
