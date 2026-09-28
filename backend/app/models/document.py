import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk

if TYPE_CHECKING:
    from app.models.document_section import DocumentSection
    from app.models.extraction import Extraction


class DocumentStatus(enum.StrEnum):
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minio_bucket: Mapped[str] = mapped_column(String, nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=DocumentStatus.UPLOADING.value)

    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    extractions: Mapped[list["Extraction"]] = relationship(
        "Extraction", back_populates="document", cascade="all, delete-orphan"
    )
    sections: Mapped[list["DocumentSection"]] = relationship(
        "DocumentSection", back_populates="document", cascade="all, delete-orphan"
    )
