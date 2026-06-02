"""lineage review record

Revision ID: 0006_lineage_review_record
Revises: 0005_procedure_lineage_edge
Create Date: 2026-06-02 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0006_lineage_review_record"
down_revision: str | None = "0005_procedure_lineage_edge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lineage_review_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("review_status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewer", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("target_type", "target_id", name="uq_lineage_review_target"),
    )
    op.create_index(op.f("ix_lineage_review_record_id"), "lineage_review_record", ["id"], unique=False)
    op.create_index(op.f("ix_lineage_review_record_review_status"), "lineage_review_record", ["review_status"], unique=False)
    op.create_index(op.f("ix_lineage_review_record_target_id"), "lineage_review_record", ["target_id"], unique=False)
    op.create_index(op.f("ix_lineage_review_record_target_type"), "lineage_review_record", ["target_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lineage_review_record_target_type"), table_name="lineage_review_record")
    op.drop_index(op.f("ix_lineage_review_record_target_id"), table_name="lineage_review_record")
    op.drop_index(op.f("ix_lineage_review_record_review_status"), table_name="lineage_review_record")
    op.drop_index(op.f("ix_lineage_review_record_id"), table_name="lineage_review_record")
    op.drop_table("lineage_review_record")
