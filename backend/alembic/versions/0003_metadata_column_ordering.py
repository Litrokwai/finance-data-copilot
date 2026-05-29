"""metadata column ordering fields

Revision ID: 0003_metadata_column_ordering
Revises: 0002_procedure_lineage
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_metadata_column_ordering"
down_revision: str | None = "0002_procedure_lineage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("metadata_column", sa.Column("ordinal_position", sa.Integer(), nullable=True))
    op.add_column("metadata_column", sa.Column("is_primary_key", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_metadata_column_table_order", "metadata_column", ["table_name", "is_primary_key", "ordinal_position"])


def downgrade() -> None:
    op.drop_index("ix_metadata_column_table_order", table_name="metadata_column")
    op.drop_column("metadata_column", "is_primary_key")
    op.drop_column("metadata_column", "ordinal_position")
