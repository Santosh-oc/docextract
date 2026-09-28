from abc import ABC, abstractmethod


class VisionModelError(Exception):
    """Raised by a VisionModelProvider. Carries a truncated raw-response
    snippet (when available) so the caller can surface it for diagnosis."""

    def __init__(self, message: str, *, status_code: int | None = None, raw_snippet: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_snippet = raw_snippet


class VisionModelProvider(ABC):
    """Decouples the extraction service from any specific vision model API.
    No model-specific logic belongs in the extraction service — only here."""

    @abstractmethod
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
        """Send prompt + images in a single chat completion request and
        return the raw text response."""

    @abstractmethod
    async def list_models(self) -> list[str]: ...

    @abstractmethod
    async def test_connection(self, model: str) -> tuple[bool, str | None]:
        """Returns (success, error_message)."""
