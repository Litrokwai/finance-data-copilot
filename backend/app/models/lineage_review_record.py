from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LineageReviewRecord(Base):
    __tablename__ = "lineage_review_record"
    __table_args__ = (
        UniqueConstraint("target_type", "target_id", name="uq_lineage_review_target"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str | None] = mapped_column(String(100))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
