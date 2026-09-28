import base64

import httpx

from app.vision.base import VisionModelError, VisionModelProvider


def _truncate(text: str, limit: int = 500) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "... [truncated]"


class OpenAICompatibleProvider(VisionModelProvider):
    """Works with any OpenAI-compatible vision API (vLLM, OpenAI, DKubeX
    SecureLLM, ...). Contains no logic specific to any single model family."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def complete(
        self,
        *,
        prompt: str,
        images_png: list[bytes],
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: int,
    ) -> str:
        content: list[dict] = [{"type": "text", "text": prompt}]
        for png_bytes in images_png:
            b64 = base64.b64encode(png_bytes).decode("ascii")
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            )

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=self._headers(), json=payload
                )
        except httpx.TimeoutException as exc:
            raise VisionModelError(
                f"The Vision Model at {self.base_url} timed out after {timeout}s.", status_code=None
            ) from exc
        except httpx.RequestError as exc:
            raise VisionModelError(
                f"Could not reach the Vision Model at {self.base_url}: {exc}"
            ) from exc

        if response.status_code == 401:
            raise VisionModelError(
                "The Vision Model rejected the API key (401 Unauthorized).",
                status_code=401,
                raw_snippet=_truncate(response.text),
            )
        if response.status_code == 429:
            raise VisionModelError(
                "The Vision Model is rate-limiting requests (429 Too Many Requests).",
                status_code=429,
                raw_snippet=_truncate(response.text),
            )
        if response.status_code >= 400:
            raise VisionModelError(
                f"The Vision Model returned an error (HTTP {response.status_code}).",
                status_code=response.status_code,
                raw_snippet=_truncate(response.text),
            )

        try:
            body = response.json()
            return body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise VisionModelError(
                "The Vision Model returned a malformed chat completion response.",
                status_code=response.status_code,
                raw_snippet=_truncate(response.text),
            ) from exc

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{self.base_url}/models", headers=self._headers())
        except httpx.RequestError as exc:
            raise VisionModelError(f"Could not reach {self.base_url}/models: {exc}") from exc

        if response.status_code == 401:
            raise VisionModelError(
                "Authentication failed while fetching models (401 Unauthorized).",
                status_code=401,
                raw_snippet=_truncate(response.text),
            )
        if response.status_code >= 400:
            raise VisionModelError(
                f"Failed to fetch models (HTTP {response.status_code}).",
                status_code=response.status_code,
                raw_snippet=_truncate(response.text),
            )

        try:
            body = response.json()
            ids = [item["id"] for item in body.get("data", []) if "id" in item]
            return sorted(ids)
        except (ValueError, TypeError) as exc:
            raise VisionModelError(
                "The models endpoint returned a malformed response.",
                raw_snippet=_truncate(response.text),
            ) from exc

    async def test_connection(self, model: str) -> tuple[bool, str | None]:
        try:
            models = await self.list_models()
        except VisionModelError as exc:
            return False, exc.message
        if model and models and model not in models:
            return True, f"Connected, but model '{model}' was not found in the available models list."
        return True, None
