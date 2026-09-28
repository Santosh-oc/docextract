from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.pdf.service import PDFService
from app.storage.base import ObjectStorage
from app.storage.minio_storage import get_object_storage


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def get_storage() -> ObjectStorage:
    return get_object_storage()


def get_pdf_service() -> PDFService:
    settings: Settings = get_settings()
    return PDFService(render_dpi=settings.pdf_render_dpi)
