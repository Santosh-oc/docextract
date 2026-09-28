import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.extraction import Extraction
    from app.models.extraction_result import ExtractionResult


class ExtractionField(Base):
    __tablename__ = "extraction_fields"

    id: Mapped[uuid.UUID] = uuid_pk()
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    extraction: Mapped["Extraction"] = relationship("Extraction", back_populates="fields")
    results: Mapped[list["ExtractionResult"]] = relationship(
        "ExtractionResult", back_populates="field", cascade="all, delete-orphan"
    )
