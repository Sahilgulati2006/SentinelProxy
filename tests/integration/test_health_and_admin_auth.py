import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "SentinelProxy"


@pytest.mark.asyncio
async def test_admin_users_requires_admin_key():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/v1/admin/users")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing admin key."


@pytest.mark.asyncio
async def test_admin_users_rejects_invalid_admin_key():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/v1/admin/users",
            headers={"X-Admin-Key": "wrong_admin_key"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid admin key."