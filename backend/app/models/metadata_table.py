from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MetadataTable(Base):
    __tablename__ = "metadata_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    table_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    table_comment: Mapped[str | None] = mapped_column(Text)
    business_domain: Mapped[str | None] = mapped_column(String(100), index=True)
    owner: Mapped[str | None] = mapped_column(String(100))
    update_frequency: Mapped[str | None] = mapped_column(String(50))
    source_collected_at = mapped_column(DateTime(timezone=True))
    latest_creat_tm = mapped_column(DateTime(timezone=True))
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
