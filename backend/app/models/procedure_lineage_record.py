from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcedureLineageRecord(Base):
    __tablename__ = "procedure_lineage_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    procedure_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    procedure_schema: Mapped[str | None] = mapped_column(String(128))
    database_name: Mapped[str | None] = mapped_column(String(128))
    source_system: Mapped[str | None] = mapped_column(String(100))
    definition_hash: Mapped[str | None] = mapped_column(String(64))
    read_tables = mapped_column(JSONB, default=list)
    write_tables = mapped_column(JSONB, default=list)
    temp_tables = mapped_column(JSONB, default=list)
    lineage_edges = mapped_column(JSONB, default=list)
    statement_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)
    parse_message: Mapped[str | None] = mapped_column(Text)
    synced_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
