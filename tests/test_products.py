import pytest
from httpx import AsyncClient


PRODUCT_PAYLOAD = {
    "name": "Test Product",
    "description": "A test product",
    "price": "19.99",
    "stock": 100,
    "category": "electronics",
}


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient) -> None:
    response = await client.get("/products")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_product_requires_admin(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/products", json=PRODUCT_PAYLOAD, headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_product_admin(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == "19.99"
    assert data["stock"] == 100


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, admin_headers: dict) -> None:
    create = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    product_id = create.json()["id"]
    response = await client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, admin_headers: dict) -> None:
    await client.post("/products", json={**PRODUCT_PAYLOAD, "name": "Blue Widget"}, headers=admin_headers)
    await client.post("/products", json={**PRODUCT_PAYLOAD, "name": "Red Gadget"}, headers=admin_headers)

    response = await client.get("/products?search=Widget")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Blue Widget"


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, admin_headers: dict) -> None:
    for i in range(5):
        await client.post("/products", json={**PRODUCT_PAYLOAD, "name": f"Product {i}"}, headers=admin_headers)

    response = await client.get("/products?page=1&page_size=2")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert response.json()["pages"] >= 3
