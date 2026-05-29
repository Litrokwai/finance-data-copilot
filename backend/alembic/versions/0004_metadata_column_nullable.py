"""metadata column nullable flag

Revision ID: 0004_metadata_column_nullable
Revises: 0003_metadata_column_ordering
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_metadata_column_nullable"
down_revision: str | None = "0003_metadata_column_ordering"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("metadata_column", sa.Column("is_nullable", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("metadata_column", "is_nullable")
