"""Persistence for the user-editable Vision Model configuration.

Settings entered on the Settings page must survive an ``uvicorn --reload``
restart (and the normal process lifecycle), so they are written to a JSON
file with ``0600`` permissions rather than kept only in memory. On startup
the file is loaded if present; otherwise the ``.env``-derived defaults from
``Settings`` are used as the initial values.
"""

import json
import os
import stat
import threading
from pathlib import Path

from pydantic import BaseModel

from app.config import Settings


class ModelSettings(BaseModel):
    provider: str
    api_base_url: str
    api_key: str = ""
    model_name: str
    temperature: float = 0
    max_tokens: int = 4096
    timeout: int = 120
    pdf_render_dpi: int = 150

    def masked(self) -> "ModelSettingsMasked":
        return ModelSettingsMasked(
            provider=self.provider,
            api_base_url=self.api_base_url,
            api_key_configured=bool(self.api_key),
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            pdf_render_dpi=self.pdf_render_dpi,
        )


class ModelSettingsMasked(BaseModel):
    provider: str
    api_base_url: str
    api_key_configured: bool
    model_name: str
    temperature: float
    max_tokens: int
    timeout: int
    pdf_render_dpi: int


class SettingsStore:
    """Thread-safe read/write access to the persisted model settings file."""

    def __init__(self, path: str, defaults: Settings):
        self._path = Path(path)
        self._defaults = defaults
        self._lock = threading.Lock()

    def _default_settings(self) -> ModelSettings:
        return ModelSettings(
            provider=self._defaults.model_provider,
            api_base_url=self._defaults.model_base_url,
            api_key=self._defaults.model_api_key,
            model_name=self._defaults.model_name,
            temperature=self._defaults.model_temperature,
            max_tokens=self._defaults.model_max_tokens,
            timeout=self._defaults.model_timeout,
            pdf_render_dpi=self._defaults.pdf_render_dpi,
        )

    def load(self) -> ModelSettings:
        with self._lock:
            if not self._path.exists():
                return self._default_settings()
            try:
                raw = json.loads(self._path.read_text())
                return ModelSettings.model_validate(raw)
            except (json.JSONDecodeError, ValueError):
                return self._default_settings()

    def save(self, settings: ModelSettings) -> None:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(".tmp")
            tmp_path.write_text(settings.model_dump_json(indent=2))
            os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
            tmp_path.replace(self._path)
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)


_store: SettingsStore | None = None


def get_settings_store() -> SettingsStore:
    global _store
    if _store is None:
        from app.config import get_settings

        settings = get_settings()
        _store = SettingsStore(settings.settings_file, settings)
    return _store
