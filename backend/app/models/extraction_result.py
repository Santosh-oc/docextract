import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk

if TYPE_CHECKING:
    from app.models.extraction import Extraction
    from app.models.extraction_field import ExtractionField


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extraction_fields.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[dict | list | str | float | bool | None] = mapped_column(JSONB, nullable=True)
    normalized_value: Mapped[dict | list | str | float | bool | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="NOT_FOUND")
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_section: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_box: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_value: Mapped[dict | list | str | float | bool | None] = mapped_column(JSONB, nullable=True)
    edited_value: Mapped[dict | list | str | float | bool | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    extraction: Mapped["Extraction"] = relationship("Extraction", back_populates="results")
    field: Mapped["ExtractionField"] = relationship("ExtractionField", back_populates="results")
