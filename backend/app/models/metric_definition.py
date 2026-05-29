from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MetricDefinition(Base):
    __tablename__ = "metric_definition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    metric_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[str | None] = mapped_column(Text)
    business_desc: Mapped[str | None] = mapped_column(Text)
    source_tables: Mapped[list[str] | None] = mapped_column(JSONB)
    source_columns: Mapped[list[str] | None] = mapped_column(JSONB)
    dimension: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str | None] = mapped_column(String(50))
    example_sql: Mapped[str | None] = mapped_column(Text)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
