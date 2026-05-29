"""procedure lineage edge table

Revision ID: 0005_procedure_lineage_edge
Revises: 0004_metadata_column_nullable
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_procedure_lineage_edge"
down_revision: str | None = "0004_metadata_column_nullable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "procedure_lineage_edge",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("procedure_id", sa.Integer(), sa.ForeignKey("procedure_lineage_record.id", ondelete="CASCADE"), nullable=False),
        sa.Column("procedure_name", sa.String(length=255), nullable=False),
        sa.Column("source_object", sa.String(length=512), nullable=False),
        sa.Column("target_object", sa.String(length=512), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column("source_kind", sa.String(length=50), nullable=False, server_default="table"),
        sa.Column("target_kind", sa.String(length=50), nullable=False, server_default="table"),
        sa.Column("statement_index", sa.Integer()),
        sa.Column("statement_type", sa.String(length=50)),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("statement_snippet", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_procedure_lineage_edge_procedure_id", "procedure_lineage_edge", ["procedure_id"])
    op.create_index("ix_procedure_lineage_edge_procedure_name", "procedure_lineage_edge", ["procedure_name"])
    op.create_index("ix_procedure_lineage_edge_source_object", "procedure_lineage_edge", ["source_object"])
    op.create_index("ix_procedure_lineage_edge_target_object", "procedure_lineage_edge", ["target_object"])
    op.create_index("ix_procedure_lineage_edge_relation_type", "procedure_lineage_edge", ["relation_type"])


def downgrade() -> None:
    op.drop_table("procedure_lineage_edge")
