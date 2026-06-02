"""metadata source time

Revision ID: 0007_metadata_source_time
Revises: 0006_lineage_review_record
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0007_metadata_source_time"
down_revision: str | None = "0006_lineage_review_record"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("metadata_table", sa.Column("source_collected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("metadata_table", sa.Column("latest_creat_tm", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("metadata_table", "latest_creat_tm")
    op.drop_column("metadata_table", "source_collected_at")
