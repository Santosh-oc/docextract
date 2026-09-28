import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ExtractionFieldIn(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    data_type: str = Field(examples=["String", "Integer", "Decimal", "Date", "Boolean", "Email", "Phone", "Currency"])
    required: bool = False


class CreateExtractionRequest(BaseModel):
    document_id: uuid.UUID
    fields: list[ExtractionFieldIn]
    instructions: str | None = None


class ExtractionFieldOut(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: str | None
    data_type: str
    required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class ExtractionOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    model_provider: str
    model_name: str
    instructions: str | None
    processing_time_ms: int | None
    fields_requested: int
    fields_extracted: int
    fields_not_found: int
    validation_failures: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ExtractionResultOut(BaseModel):
    id: uuid.UUID
    field_id: uuid.UUID
    field_name: str
    field_display_name: str
    value: str | float | int | bool | None
    normalized_value: str | float | int | bool | None
    confidence: float | None
    status: str
    page: int | None
    document_section: str | None
    evidence: str | None
    bounding_box: dict | None
    validation_status: str | None
    is_verified: bool
    is_user_edited: bool
    original_value: str | float | int | bool | None
    edited_value: str | float | int | bool | None


class ExtractionResultResponse(BaseModel):
    extraction: ExtractionOut
    results: list[ExtractionResultOut]
