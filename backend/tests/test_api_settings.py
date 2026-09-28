import httpx
import pytest
import respx


@pytest.mark.asyncio
async def test_get_model_settings_never_exposes_raw_key(client):
    resp = await client.get("/api/settings/model")
    assert resp.status_code == 200
    body = resp.json()
    assert "api_key" not in body
    assert "api_key_configured" in body


@pytest.mark.asyncio
async def test_put_model_settings_round_trips(client):
    payload = {
        "provider": "openai_compatible",
        "api_base_url": "http://mock-vision.test/v1",
        "api_key": "super-secret",
        "model_name": "test-model",
        "temperature": 0.2,
        "max_tokens": 2048,
        "timeout": 60,
        "pdf_render_dpi": 200,
    }
    resp = await client.put("/api/settings/model", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_name"] == "test-model"
    assert body["api_key_configured"] is True
    assert "super-secret" not in resp.text


@pytest.mark.asyncio
async def test_put_without_api_key_preserves_existing_key(client):
    await client.put(
        "/api/settings/model",
        json={
            "provider": "openai_compatible",
            "api_base_url": "http://mock-vision.test/v1",
            "api_key": "keep-me",
            "model_name": "m1",
        },
    )
    resp = await client.put(
        "/api/settings/model",
        json={
            "provider": "openai_compatible",
            "api_base_url": "http://mock-vision.test/v1",
            "api_key": "",
            "model_name": "m2",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["api_key_configured"] is True


@pytest.mark.asyncio
@respx.mock
async def test_fetch_models_endpoint(client):
    respx.get("http://mock-vision.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "z"}, {"id": "a"}]})
    )
    resp = await client.post(
        "/api/settings/model/models", json={"api_base_url": "http://mock-vision.test/v1", "api_key": "k"}
    )
    assert resp.status_code == 200
    assert resp.json()["models"] == ["a", "z"]


@pytest.mark.asyncio
@respx.mock
async def test_fetch_models_auth_failure_returns_friendly_error(client):
    respx.get("http://mock-vision.test/v1/models").mock(return_value=httpx.Response(401, text="nope"))
    resp = await client.post(
        "/api/settings/model/models", json={"api_base_url": "http://mock-vision.test/v1", "api_key": "bad"}
    )
    assert resp.status_code >= 400
    assert "error" in resp.json()


@pytest.mark.asyncio
@respx.mock
async def test_connection_success(client):
    await client.put(
        "/api/settings/model",
        json={
            "provider": "openai_compatible",
            "api_base_url": "http://mock-vision.test/v1",
            "api_key": "k",
            "model_name": "m",
        },
    )
    respx.get("http://mock-vision.test/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "m"}]})
    )
    resp = await client.post("/api/settings/model/test")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["response_time_seconds"] is not None
