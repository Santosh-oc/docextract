import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_pdf_service, get_storage
from app.pdf.service import PDFService
from app.schemas.extraction import (
    CreateExtractionRequest,
    ExtractionOut,
    ExtractionResultOut,
    ExtractionResultResponse,
)
from app.services import extraction_service
from app.services.settings_service import build_provider, get_current_settings
from app.storage.base import ObjectStorage

router = APIRouter(prefix="/api/extractions", tags=["extractions"])


@router.post("", response_model=ExtractionOut)
async def create_extraction(
    payload: CreateExtractionRequest,
    db: AsyncSession = Depends(get_db_session),
    storage: ObjectStorage = Depends(get_storage),
    pdf_service: PDFService = Depends(get_pdf_service),
):
    model_settings = get_current_settings()
    provider = build_provider(model_settings.api_base_url, model_settings.api_key)
    extraction = await extraction_service.create_and_run_extraction(
        db,
        storage,
        pdf_service,
        provider,
        model_settings,
        document_id=payload.document_id,
        fields=[f.model_dump() for f in payload.fields],
        instructions=payload.instructions,
    )
    return ExtractionOut.model_validate(extraction)


@router.get("/{extraction_id}", response_model=ExtractionOut)
async def get_extraction(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)):
    extraction = await extraction_service.get_extraction(db, extraction_id)
    return ExtractionOut.model_validate(extraction)


def _build_result_response(extraction) -> ExtractionResultResponse:
    fields_by_id = {f.id: f for f in extraction.fields}
    results = []
    for r in extraction.results:
        field = fields_by_id.get(r.field_id)
        results.append(
            ExtractionResultOut(
                id=r.id,
                field_id=r.field_id,
                field_name=field.name if field else "",
                field_display_name=field.display_name if field else "",
                value=r.value,
                normalized_value=r.normalized_value,
                confidence=float(r.confidence) if r.confidence is not None else None,
                status=r.status,
                page=r.page,
                document_section=r.document_section,
                evidence=r.evidence,
                bounding_box=r.bounding_box,
                validation_status=r.validation_status,
                is_verified=r.is_verified,
                is_user_edited=r.is_user_edited,
                original_value=r.original_value,
                edited_value=r.edited_value,
            )
        )
    order = {f.id: f.sort_order for f in extraction.fields}
    results.sort(key=lambda r: order.get(r.field_id, 0))
    return ExtractionResultResponse(extraction=ExtractionOut.model_validate(extraction), results=results)


@router.get("/{extraction_id}/result", response_model=ExtractionResultResponse)
async def get_extraction_result(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)):
    extraction = await extraction_service.get_extraction(db, extraction_id)
    return _build_result_response(extraction)


@router.get("/{extraction_id}/download/json")
async def download_extraction_json(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)):
    extraction = await extraction_service.get_extraction(db, extraction_id)
    data = extraction_service.to_json_download(extraction)
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="extraction_{extraction_id}.json"'},
    )


@router.get("/{extraction_id}/download/csv")
async def download_extraction_csv(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)):
    extraction = await extraction_service.get_extraction(db, extraction_id)
    data = extraction_service.to_csv_download(extraction)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="extraction_{extraction_id}.csv"'},
    )
