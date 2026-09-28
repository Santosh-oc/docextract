from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Static, deployment-level configuration loaded from the environment.

    Runtime-editable model/provider configuration (base URL, API key, model
    name, ...) lives separately in ``SettingsStore`` so it can be changed from
    the Settings page without restarting the process.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    max_pdf_size_mb: int = 25

    model_provider: str = "openai_compatible"
    model_base_url: str = "http://localhost:8000/v1"
    model_name: str = "vision-model"
    model_api_key: str = ""
    model_timeout: int = 120
    model_temperature: float = 0
    model_max_tokens: int = 4096

    pdf_render_dpi: int = 150

    settings_file: str = "./.data/model_settings.json"

    # When true (the DKubeX platform chart sets this), every request other than /api/health
    # must carry X-Auth-Request-User, injected by the platform's gateway. Off by default so
    # local development and the workspace-app tile (neither behind that gateway) are unaffected.
    platform_auth_required: bool = False

    database_url: str = (
        "postgresql+asyncpg://document_extractor:document_extractor@localhost:5432/document_extractor"
    )

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_documents: str = "documents"

    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
