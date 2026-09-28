import csv
import io
import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import (
    ModelNotConfiguredError,
    NotFoundError,
    ValidationAppError,
    VisionProviderError,
)
from app.core.logging import Timer, get_logger
from app.models.document import Document, DocumentStatus
from app.models.extraction import Extraction, ExtractionStatus
from app.models.extraction_field import ExtractionField
from app.models.extraction_result import ExtractionResult
from app.pdf.service import PDFService
from app.services.field_validation import validate_field_value
from app.settings_store import ModelSettings
from app.storage.base import ObjectStorage
from app.vision.base import VisionModelError, VisionModelProvider
from app.vision.prompt import build_extraction_prompt
from app.vision.response_schema import ResponseParseError, parse_extraction_response

logger = get_logger(__name__)


async def create_and_run_extraction(
    db: AsyncSession,
    storage: ObjectStorage,
    pdf_service: PDFService,
    provider: VisionModelProvider,
    model_settings: ModelSettings,
    *,
    document_id: uuid.UUID,
    fields: list[dict],
    instructions: str | None,
) -> Extraction:
    if not model_settings.api_base_url or not model_settings.model_name:
        raise ModelNotConfiguredError("Configure the Vision Model in Settings before extracting.")
    if not fields:
        raise ValidationAppError("At least one field must be defined before extraction.")

    document = await db.get(Document, document_id)
    if document is None or document.status == DocumentStatus.DELETED.value:
        raise NotFoundError("Document not found.")

    extraction = Extraction(
        document_id=document_id,
        status=ExtractionStatus.PROCESSING.value,
        model_provider=model_settings.provider,
        model_name=model_settings.model_name,
        instructions=instructions,
        fields_requested=len(fields),
    )
    extraction.fields = [
        ExtractionField(
            name=f["name"],
            display_name=f["display_name"],
            description=f.get("description"),
            data_type=f["data_type"],
            required=f.get("required", False),
            sort_order=idx,
        )
        for idx, f in enumerate(fields)
    ]
    db.add(extraction)
    document.status = DocumentStatus.PROCESSING.value
    await db.flush()

    timer = Timer()
    try:
        # Preparing PDF / rendering pages
        pdf_bytes = storage.download(document.minio_bucket, document.minio_object_key)
        images = pdf_service.render_all_pages(pdf_bytes)

        prompt = build_extraction_prompt(fields, instructions)

        # Sending document to Vision Model / processing extraction
        raw_response = await provider.complete(
            prompt=prompt,
            images_png=images,
            model=model_settings.model_name,
            temperature=model_settings.temperature,
            max_tokens=model_settings.max_tokens,
            timeout=model_settings.timeout,
        )

        # Validating results
        parsed = parse_extraction_response(raw_response)
    except (VisionModelError, ResponseParseError) as exc:
        extraction.status = ExtractionStatus.FAILED.value
        extraction.error_message = exc.message
        extraction.processing_time_ms = timer.elapsed_ms
        document.status = DocumentStatus.FAILED.value
        await db.commit()
        logger.error(
            "extraction failed",
            extra={
                "operation": "extraction",
                "document_id": str(document_id),
                "model": model_settings.model_name,
                "status": "FAILED",
            },
        )
        raise VisionProviderError(exc.message, detail=getattr(exc, "raw_snippet", None)) from exc

    by_name = {f.name: f for f in extraction.fields}
    fields_extracted = 0
    fields_not_found = 0
    validation_failures = 0

    for item in parsed.fields:
        field = by_name.get(item.name)
        if field is None:
            continue
        validated = validate_field_value(field.data_type, item.value)
        status = "NOT_FOUND" if item.value is None else "FOUND"
        if item.value is not None:
            fields_extracted += 1
        else:
            fields_not_found += 1
        if validated.validation_status == "INVALID_FORMAT" or (
            field.required and item.value is None
        ):
            validation_failures += 1
            if field.required and item.value is None:
                validated.validation_status = "MISSING_REQUIRED"

        db.add(
            ExtractionResult(
                extraction_id=extraction.id,
                field_id=field.id,
                value=item.value,
                normalized_value=validated.normalized_value,
                confidence=item.confidence,
                status=status,
                page=item.page,
                evidence=item.evidence,
                validation_status=validated.validation_status,
            )
        )

    # Any requested field the model omitted entirely from its response
    responded_names = {item.name for item in parsed.fields}
    for field in extraction.fields:
        if field.name not in responded_names:
            fields_not_found += 1
            validation_status = "MISSING_REQUIRED" if field.required else "NOT_FOUND"
            if field.required:
                validation_failures += 1
            db.add(
                ExtractionResult(
                    extraction_id=extraction.id,
                    field_id=field.id,
                    value=None,
                    status="NOT_FOUND",
                    validation_status=validation_status,
                )
            )

    extraction.status = ExtractionStatus.COMPLETED.value
    extraction.fields_extracted = fields_extracted
    extraction.fields_not_found = fields_not_found
    extraction.validation_failures = validation_failures
    extraction.processing_time_ms = timer.elapsed_ms
    extraction.completed_at = func.now()
    document.status = DocumentStatus.COMPLETED.value

    await db.commit()
    await db.refresh(extraction)
    logger.info(
        "extraction completed",
        extra={
            "operation": "extraction",
            "document_id": str(document_id),
            "extraction_id": str(extraction.id),
            "model": model_settings.model_name,
            "processing_time_ms": extraction.processing_time_ms,
            "status": "COMPLETED",
        },
    )
    return extraction


async def get_extraction(db: AsyncSession, extraction_id: uuid.UUID) -> Extraction:
    extraction = await db.get(
        Extraction, extraction_id, options=[selectinload(Extraction.fields), selectinload(Extraction.results)]
    )
    if extraction is None:
        raise NotFoundError("Extraction not found.")
    return extraction


async def list_extractions_for_document(db: AsyncSession, document_id: uuid.UUID) -> list[Extraction]:
    result = await db.execute(
        select(Extraction)
        .where(Extraction.document_id == document_id)
        .order_by(Extraction.created_at.desc())
    )
    return list(result.scalars().all())


def build_result_rows(extraction: Extraction) -> list[dict]:
    fields_by_id = {f.id: f for f in extraction.fields}
    rows = []
    for result in extraction.results:
        field = fields_by_id.get(result.field_id)
        rows.append(
            {
                "field_name": field.name if field else "",
                "field_display_name": field.display_name if field else "",
                "value": result.value,
                "normalized_value": result.normalized_value,
                "confidence": float(result.confidence) if result.confidence is not None else None,
                "status": result.status,
                "page": result.page,
                "evidence": result.evidence,
                "validation_status": result.validation_status,
            }
        )
    return rows


def to_json_download(extraction: Extraction) -> bytes:
    payload = {
        "extraction_id": str(extraction.id),
        "document_id": str(extraction.document_id),
        "model_name": extraction.model_name,
        "created_at": extraction.created_at.isoformat() if extraction.created_at else None,
        "fields": build_result_rows(extraction),
    }
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def to_csv_download(extraction: Extraction) -> bytes:
    rows = build_result_rows(extraction)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "field_name",
            "field_display_name",
            "value",
            "normalized_value",
            "confidence",
            "status",
            "page",
            "evidence",
            "validation_status",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")
