"""procedure lineage records

Revision ID: 0002_procedure_lineage
Revises: 0001_initial_schema
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_procedure_lineage"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "procedure_lineage_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("procedure_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("procedure_schema", sa.String(length=128)),
        sa.Column("database_name", sa.String(length=128)),
        sa.Column("source_system", sa.String(length=100)),
        sa.Column("definition_hash", sa.String(length=64)),
        sa.Column("read_tables", postgresql.JSONB(), server_default="[]"),
        sa.Column("write_tables", postgresql.JSONB(), server_default="[]"),
        sa.Column("temp_tables", postgresql.JSONB(), server_default="[]"),
        sa.Column("lineage_edges", postgresql.JSONB(), server_default="[]"),
        sa.Column("statement_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parse_status", sa.String(length=50), nullable=False, server_default="SUCCESS"),
        sa.Column("parse_message", sa.Text()),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_procedure_lineage_record_procedure_name", "procedure_lineage_record", ["procedure_name"])
    op.create_index("ix_procedure_lineage_record_synced_at", "procedure_lineage_record", ["synced_at"])


def downgrade() -> None:
    op.drop_table("procedure_lineage_record")
