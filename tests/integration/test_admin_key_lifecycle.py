import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_admin_can_create_key_and_revoke_it():
    transport = ASGITransport(app=app)
    admin_headers = {
        "X-Admin-Key": settings.SENTINEL_ADMIN_KEY,
    }

    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        # 1. Create user
        create_user_response = await client.post(
            "/v1/admin/users",
            headers=admin_headers,
            json={
                "email": unique_email,
                "monthly_token_limit": 50000,
            },
        )

        assert create_user_response.status_code == 200
        created_user = create_user_response.json()

        assert created_user["email"] == unique_email
        assert created_user["monthly_token_limit"] == 50000
        assert created_user["is_active"] is True

        user_id = created_user["id"]

        # 2. Create API key for user
        create_key_response = await client.post(
            "/v1/admin/api-keys",
            headers=admin_headers,
            json={
                "user_id": user_id,
                "name": "integration-test-key",
            },
        )

        assert create_key_response.status_code == 200
        created_key = create_key_response.json()

        assert created_key["user_id"] == user_id
        assert created_key["name"] == "integration-test-key"
        assert created_key["is_active"] is True
        assert created_key["api_key"].startswith("sp_live_")
        assert created_key["key_prefix"] == created_key["api_key"][:16]

        full_api_key = created_key["api_key"]
        key_id = created_key["id"]

        # 3. API key can access /v1/me
        me_response = await client.get(
            "/v1/me",
            headers={
                "Authorization": f"Bearer {full_api_key}",
            },
        )

        assert me_response.status_code == 200
        me = me_response.json()

        assert me["user_id"] == user_id
        assert me["email"] == unique_email
        assert me["api_key_prefix"] == created_key["key_prefix"]
        assert me["budget"]["monthly_token_limit"] == 50000

        # 4. Revoke key
        revoke_response = await client.post(
            f"/v1/admin/api-keys/{key_id}/revoke",
            headers=admin_headers,
        )

        assert revoke_response.status_code == 200
        revoked_key = revoke_response.json()

        assert revoked_key["id"] == key_id
        assert revoked_key["is_active"] is False

        # 5. Revoked key can no longer access /v1/me
        revoked_me_response = await client.get(
            "/v1/me",
            headers={
                "Authorization": f"Bearer {full_api_key}",
            },
        )

        assert revoked_me_response.status_code == 401
        assert revoked_me_response.json()["detail"] == "Invalid API key."