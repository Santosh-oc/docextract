from pydantic import BaseModel, Field


class ModelSettingsIn(BaseModel):
    provider: str = Field(examples=["openai_compatible", "dkubex"])
    api_base_url: str
    api_key: str | None = None
    model_name: str
    temperature: float = 0
    max_tokens: int = 4096
    timeout: int = 120
    pdf_render_dpi: int = 150


class ModelSettingsOut(BaseModel):
    provider: str
    api_base_url: str
    api_key_configured: bool
    model_name: str
    temperature: float
    max_tokens: int
    timeout: int
    pdf_render_dpi: int


class ModelListRequest(BaseModel):
    api_base_url: str
    api_key: str | None = None


class ModelListResponse(BaseModel):
    models: list[str]


class TestConnectionResponse(BaseModel):
    success: bool
    model: str | None = None
    response_time_seconds: float | None = None
    message: str | None = None
