import json

import httpx
import pytest
import respx

from app.vision.base import VisionModelError
from app.vision.openai_compatible import OpenAICompatibleProvider

BASE_URL = "http://mock-vision.test/v1"


@pytest.mark.asyncio
@respx.mock
async def test_complete_success():
    respx.post(f"{BASE_URL}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps({"fields": []})}}]},
        )
    )
    provider = OpenAICompatibleProvider(BASE_URL, "key")
    result = await provider.complete(
        prompt="p", images_png=[b"\x89PNG"], model="m", temperature=0, max_tokens=100, timeout=10
    )
    assert json.loads(result) == {"fields": []}


@pytest.mark.asyncio
@respx.mock
async def test_complete_auth_error():
    respx.post(f"{BASE_URL}/chat/completions").mock(return_value=httpx.Response(401, text="unauthorized"))
    provider = OpenAICompatibleProvider(BASE_URL, "bad-key")
    with pytest.raises(VisionModelError) as exc_info:
        await provider.complete(prompt="p", images_png=[], model="m", temperature=0, max_tokens=100, timeout=10)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@respx.mock
async def test_complete_rate_limit():
    respx.post(f"{BASE_URL}/chat/completions").mock(return_value=httpx.Response(429, text="slow down"))
    provider = OpenAICompatibleProvider(BASE_URL, "key")
    with pytest.raises(VisionModelError) as exc_info:
        await provider.complete(prompt="p", images_png=[], model="m", temperature=0, max_tokens=100, timeout=10)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
@respx.mock
async def test_complete_timeout():
    respx.post(f"{BASE_URL}/chat/completions").mock(side_effect=httpx.TimeoutException("timed out"))
    provider = OpenAICompatibleProvider(BASE_URL, "key")
    with pytest.raises(VisionModelError):
        await provider.complete(prompt="p", images_png=[], model="m", temperature=0, max_tokens=100, timeout=1)


@pytest.mark.asyncio
@respx.mock
async def test_complete_malformed_response():
    respx.post(f"{BASE_URL}/chat/completions").mock(return_value=httpx.Response(200, json={"nonsense": True}))
    provider = OpenAICompatibleProvider(BASE_URL, "key")
    with pytest.raises(VisionModelError) as exc_info:
        await provider.complete(prompt="p", images_png=[], model="m", temperature=0, max_tokens=100, timeout=10)
    assert exc_info.value.raw_snippet is not None


@pytest.mark.asyncio
@respx.mock
async def test_list_models_sorted():
    respx.get(f"{BASE_URL}/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "b-model"}, {"id": "a-model"}]})
    )
    provider = OpenAICompatibleProvider(BASE_URL, "key")
    models = await provider.list_models()
    assert models == ["a-model", "b-model"]


@pytest.mark.asyncio
@respx.mock
async def test_test_connection_success():
    respx.get(f"{BASE_URL}/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "m"}]})
    )
    provider = OpenAICompatibleProvider(BASE_URL, "key")
    success, message = await provider.test_connection("m")
    assert success is True
    assert message is None
