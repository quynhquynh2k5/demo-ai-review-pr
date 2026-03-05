import pytest
from httpx import AsyncClient

COUPON_PAYLOAD = {
    "code": "SAVE10",
    "discount_percent": "10.00",
    "max_uses": 100,
}

PRODUCT_PAYLOAD = {
    "name": "Coupon Test Product",
    "description": "For coupon testing",
    "price": "100.00",
    "stock": 50,
    "category": "test",
}


@pytest.mark.asyncio
async def test_create_coupon_requires_admin(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/coupons", json=COUPON_PAYLOAD, headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_coupon(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.post("/coupons", json=COUPON_PAYLOAD, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["code"] == "SAVE10"
    assert response.json()["discount_percent"] == "10.00"


@pytest.mark.asyncio
async def test_coupon_discount_over_100_rejected(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.post(
        "/coupons",
        json={"code": "INVALID", "discount_percent": "110.00", "max_uses": 10},
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_checkout_with_coupon(client: AsyncClient, auth_headers: dict, admin_headers: dict) -> None:
    await client.post("/coupons", json=COUPON_PAYLOAD, headers=admin_headers)
    product = await client.post("/products", json=PRODUCT_PAYLOAD, headers=admin_headers)
    product_id = product.json()["id"]

    await client.post("/cart/items", json={"product_id": product_id, "quantity": 1}, headers=auth_headers)
    response = await client.post("/orders/checkout", json={"coupon_code": "SAVE10"}, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert float(data["discount_amount"]) > 0
