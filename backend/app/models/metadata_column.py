from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MetadataColumn(Base):
    __tablename__ = "metadata_column"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ordinal_position: Mapped[int | None] = mapped_column(Integer)
    data_type: Mapped[str | None] = mapped_column(String(100))
    column_comment: Mapped[str | None] = mapped_column(Text)
    business_desc: Mapped[str | None] = mapped_column(Text)
    example_value: Mapped[str | None] = mapped_column(Text)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_nullable: Mapped[bool | None] = mapped_column(Boolean)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
