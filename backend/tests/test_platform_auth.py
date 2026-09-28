import pytest

import app.main as main_module


@pytest.fixture
def with_platform_auth_required():
    main_module.settings.platform_auth_required = True
    try:
        yield
    finally:
        main_module.settings.platform_auth_required = False


@pytest.mark.asyncio
async def test_health_exempt_even_when_auth_required(client, with_platform_auth_required):
    resp = await client.get("/api/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_missing_auth_header_rejected_when_required(client, with_platform_auth_required):
    resp = await client.get("/api/settings/model")
    assert resp.status_code == 401
    assert resp.json()["error"] == "Not authenticated"


@pytest.mark.asyncio
async def test_auth_header_present_is_allowed_through(client, with_platform_auth_required):
    resp = await client.get("/api/settings/model", headers={"X-Auth-Request-User": "alice"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_not_enforced_by_default(client):
    resp = await client.get("/api/settings/model")
    assert resp.status_code == 200
