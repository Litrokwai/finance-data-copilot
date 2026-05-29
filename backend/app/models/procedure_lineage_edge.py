from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcedureLineageEdge(Base):
    __tablename__ = "procedure_lineage_edge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    procedure_id: Mapped[int] = mapped_column(ForeignKey("procedure_lineage_record.id", ondelete="CASCADE"), nullable=False, index=True)
    procedure_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_object: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    target_object: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="table")
    target_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="table")
    statement_index: Mapped[int | None] = mapped_column(Integer)
    statement_type: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    statement_snippet: Mapped[str | None] = mapped_column(Text)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
