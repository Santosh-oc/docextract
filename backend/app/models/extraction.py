import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, uuid_pk

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.extraction_field import ExtractionField
    from app.models.extraction_result import ExtractionResult


class ExtractionStatus(enum.StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default=ExtractionStatus.PENDING.value)
    model_provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fields_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fields_extracted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fields_not_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = created_at_col()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="extractions")
    fields: Mapped[list["ExtractionField"]] = relationship(
        "ExtractionField",
        back_populates="extraction",
        cascade="all, delete-orphan",
        order_by="ExtractionField.sort_order",
    )
    results: Mapped[list["ExtractionResult"]] = relationship(
        "ExtractionResult", back_populates="extraction", cascade="all, delete-orphan"
    )
