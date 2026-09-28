import uuid

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_pdf_service, get_storage
from app.core.errors import ValidationAppError
from app.pdf.service import PDFService
from app.schemas.document import DocumentOut, DocumentUploadResponse
from app.services import document_service
from app.storage.base import ObjectStorage

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db_session),
    storage: ObjectStorage = Depends(get_storage),
    pdf_service: PDFService = Depends(get_pdf_service),
):
    if file.content_type != "application/pdf":
        raise ValidationAppError("Only PDF documents are supported.")
    data = await file.read()
    document = await document_service.upload_document(
        db, storage, pdf_service, filename=file.filename or "document.pdf", mime_type=file.content_type, data=data
    )
    return DocumentUploadResponse(document=DocumentOut.model_validate(document))


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)):
    document = await document_service.get_document(db, document_id)
    return DocumentOut.model_validate(document)


@router.get("/{document_id}/pages/{page_num}")
async def get_document_page(
    document_id: uuid.UUID,
    page_num: int,
    db: AsyncSession = Depends(get_db_session),
    storage: ObjectStorage = Depends(get_storage),
    pdf_service: PDFService = Depends(get_pdf_service),
):
    png_bytes = await document_service.render_page_image(db, storage, pdf_service, document_id, page_num)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    storage: ObjectStorage = Depends(get_storage),
):
    document = await document_service.get_document(db, document_id)
    data = await document_service.get_original_pdf_bytes(db, storage, document_id)
    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'},
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    storage: ObjectStorage = Depends(get_storage),
):
    await document_service.delete_document(db, storage, document_id)
    return {"status": "deleted"}
