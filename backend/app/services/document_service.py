import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.errors import NotFoundError, StorageError, ValidationAppError
from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus
from app.pdf.service import PDFService, PDFValidationError
from app.storage.base import ObjectStorage

logger = get_logger(__name__)


def object_key_for(document_id: uuid.UUID) -> str:
    return f"documents/{document_id}/original.pdf"


async def upload_document(
    db: AsyncSession,
    storage: ObjectStorage,
    pdf_service: PDFService,
    *,
    filename: str,
    mime_type: str,
    data: bytes,
) -> Document:
    settings = get_settings()

    if mime_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        raise ValidationAppError("Only PDF documents are supported.")

    max_bytes = settings.max_pdf_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise ValidationAppError(f"PDF exceeds the maximum allowed size of {settings.max_pdf_size_mb} MB.")

    try:
        pdf_service.validate_pdf(data)
        page_count = pdf_service.get_page_count(data)
    except PDFValidationError as exc:
        raise ValidationAppError(str(exc)) from exc

    document_id = uuid.uuid4()
    bucket = settings.minio_bucket_documents
    object_key = object_key_for(document_id)

    try:
        storage.upload(bucket, object_key, data, content_type="application/pdf")
    except StorageError:
        logger.error("upload to object storage failed", extra={"operation": "upload", "doc_filename": filename})
        raise

    document = Document(
        id=document_id,
        original_filename=filename,
        mime_type=mime_type,
        file_size=len(data),
        page_count=page_count,
        minio_bucket=bucket,
        minio_object_key=object_key,
        status=DocumentStatus.UPLOADED.value,
    )
    db.add(document)
    try:
        await db.commit()
    except Exception:
        # PostgreSQL persistence failed after a successful MinIO upload: clean
        # up the orphaned object rather than silently losing track of it.
        await db.rollback()
        try:
            storage.delete(bucket, object_key)
        except StorageError:
            logger.error(
                "failed to clean up orphaned object after DB failure",
                extra={"operation": "upload_cleanup", "doc_filename": filename},
            )
        raise

    await db.refresh(document)
    logger.info(
        "document uploaded",
        extra={
            "operation": "upload",
            "doc_filename": filename,
            "page_count": page_count,
            "document_id": str(document_id),
        },
    )
    return document


async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Document:
    document = await db.get(Document, document_id)
    if document is None or document.status == DocumentStatus.DELETED.value:
        raise NotFoundError("Document not found.")
    return document


async def get_original_pdf_bytes(db: AsyncSession, storage: ObjectStorage, document_id: uuid.UUID) -> bytes:
    document = await get_document(db, document_id)
    return storage.download(document.minio_bucket, document.minio_object_key)


async def render_page_image(
    db: AsyncSession,
    storage: ObjectStorage,
    pdf_service: PDFService,
    document_id: uuid.UUID,
    page_number: int,
) -> bytes:
    document = await get_document(db, document_id)
    data = storage.download(document.minio_bucket, document.minio_object_key)
    try:
        return pdf_service.render_page(data, page_number)
    except PDFValidationError as exc:
        raise ValidationAppError(str(exc)) from exc


async def delete_document(db: AsyncSession, storage: ObjectStorage, document_id: uuid.UUID) -> None:
    document = await get_document(db, document_id)
    storage.delete(document.minio_bucket, document.minio_object_key)
    await db.delete(document)
    await db.commit()
    logger.info("document deleted", extra={"operation": "delete", "document_id": str(document_id)})
