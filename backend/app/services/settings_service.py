from app.settings_store import ModelSettings, get_settings_store
from app.vision.base import VisionModelProvider
from app.vision.openai_compatible import OpenAICompatibleProvider


def get_current_settings() -> ModelSettings:
    return get_settings_store().load()


def save_settings(settings: ModelSettings) -> ModelSettings:
    store = get_settings_store()
    # Preserve the previously configured API key if the caller left it blank
    # (the UI never round-trips the real key back to the client).
    if not settings.api_key:
        existing = store.load()
        settings.api_key = existing.api_key
    store.save(settings)
    return settings


def build_provider(api_base_url: str, api_key: str | None) -> VisionModelProvider:
    return OpenAICompatibleProvider(base_url=api_base_url, api_key=api_key or "")
