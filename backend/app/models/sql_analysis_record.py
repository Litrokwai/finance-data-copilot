from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SqlAnalysisRecord(Base):
    __tablename__ = "sql_analysis_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_sql: Mapped[str] = mapped_column(Text, nullable=False)
    sql_type: Mapped[str | None] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(Text)
    involved_tables: Mapped[list[str] | None] = mapped_column(JSONB)
    involved_columns: Mapped[list[str] | None] = mapped_column(JSONB)
    join_relations: Mapped[list[dict] | None] = mapped_column(JSONB)
    where_conditions: Mapped[list[str] | None] = mapped_column(JSONB)
    risk_level: Mapped[str | None] = mapped_column(String(20), index=True)
    risk_items: Mapped[list[str] | None] = mapped_column(JSONB)
    analysis_result_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
