import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={"email": "user@example.com", "password": "password123"})
    assert response.status_code == 201
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    response = await client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
    response = await client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "wrong@example.com", "password": "password123"})
    response = await client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrongpass"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["is_admin"] is False


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_cannot_set_is_admin(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "hacker@example.com", "password": "password123", "is_admin": True},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["is_admin"] is False
