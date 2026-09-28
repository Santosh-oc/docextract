import time

from fastapi import APIRouter

from app.core.errors import VisionProviderError
from app.schemas.settings import (
    ModelListRequest,
    ModelListResponse,
    ModelSettingsIn,
    ModelSettingsOut,
    TestConnectionResponse,
)
from app.services.settings_service import (
    build_provider,
    get_current_settings,
    save_settings,
)
from app.settings_store import ModelSettings
from app.vision.base import VisionModelError

router = APIRouter(prefix="/api/settings/model", tags=["settings"])


@router.get("", response_model=ModelSettingsOut)
async def get_model_settings():
    return get_current_settings().masked()


@router.put("", response_model=ModelSettingsOut)
async def put_model_settings(payload: ModelSettingsIn):
    settings = ModelSettings(
        provider=payload.provider,
        api_base_url=payload.api_base_url,
        api_key=payload.api_key or "",
        model_name=payload.model_name,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        timeout=payload.timeout,
        pdf_render_dpi=payload.pdf_render_dpi,
    )
    saved = save_settings(settings)
    return saved.masked()


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection():
    settings = get_current_settings()
    if not settings.api_base_url or not settings.model_name:
        return TestConnectionResponse(success=False, message="Configure the API Base URL and Model first.")

    provider = build_provider(settings.api_base_url, settings.api_key)
    start = time.perf_counter()
    try:
        success, message = await provider.test_connection(settings.model_name)
    except VisionModelError as exc:
        return TestConnectionResponse(success=False, message=exc.message)
    elapsed = time.perf_counter() - start
    return TestConnectionResponse(
        success=success,
        model=settings.model_name if success else None,
        response_time_seconds=round(elapsed, 2),
        message=message,
    )


@router.post("/models", response_model=ModelListResponse)
async def fetch_models(payload: ModelListRequest):
    provider = build_provider(payload.api_base_url, payload.api_key)
    try:
        models = await provider.list_models()
    except VisionModelError as exc:
        raise VisionProviderError(exc.message, detail=exc.raw_snippet) from exc
    return ModelListResponse(models=models)
