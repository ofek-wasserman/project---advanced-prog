from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient

from src.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_returns_200_and_user_id(client: AsyncClient) -> None:
    resp = await client.post("/register", json={"payment_token": "tok_123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "user_id" in body
    assert isinstance(body["user_id"], int)

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

@pytest.mark.asyncio
async def test_register_missing_payment_token_returns_400(client: AsyncClient) -> None:
    resp = await client.post("/register", json={})
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_register_duplicate_token_returns_400(client: AsyncClient) -> None:
    await client.post("/register", json={"payment_token": "dup"})
    resp = await client.post("/register", json={"payment_token": "dup"})
    assert resp.status_code == 400