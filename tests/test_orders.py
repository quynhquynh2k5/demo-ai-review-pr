import pytest
from httpx import AsyncClient

PRODUCT_PAYLOAD = {
    "name": "Checkout Product",
    "description": "For testing checkout",
    "price": "50.00",
    "stock": 10,
    "category": "test",
}


@pytest.mark.asyncio
async def test_checkout_empty_cart(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/orders/checkout", json={}, headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_checkout_success(client: AsyncClient, auth_headers: dict, admin_headers: dict) -> None:
    product = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    product_id = product.json()["id"]

    await client.post("/cart/items", json={"product_id": product_id, "quantity": 2}, headers=auth_headers)

    response = await client.post("/orders/checkout", json={}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_checkout_clears_cart(client: AsyncClient, auth_headers: dict, admin_headers: dict) -> None:
    product = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    product_id = product.json()["id"]

    await client.post("/cart/items", json={"product_id": product_id, "quantity": 1}, headers=auth_headers)
    await client.post("/orders/checkout", json={}, headers=auth_headers)

    cart = await client.get("/cart", headers=auth_headers)
    assert cart.json()["items"] == []


@pytest.mark.asyncio
async def test_get_order_only_own(client: AsyncClient, auth_headers: dict, admin_headers: dict) -> None:
    product = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    product_id = product.json()["id"]
    await client.post("/cart/items", json={"product_id": product_id, "quantity": 1}, headers=auth_headers)
    order = await client.post("/orders/checkout", json={}, headers=auth_headers)
    order_id = order.json()["id"]

    # Register another user and try to access the order
    await client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    login = await client.post("/auth/login", json={"email": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get(f"/orders/{order_id}", headers=other_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient, auth_headers: dict, admin_headers: dict) -> None:
    product = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    product_id = product.json()["id"]
    await client.post("/cart/items", json={"product_id": product_id, "quantity": 2}, headers=auth_headers)
    order = await client.post("/orders/checkout", json={}, headers=auth_headers)
    order_id = order.json()["id"]

    response = await client.put(f"/orders/{order_id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
