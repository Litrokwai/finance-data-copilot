"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN
                CREATE EXTENSION IF NOT EXISTS vector;
            ELSE
                RAISE NOTICE 'pgvector extension is not installed locally; skip vector extension for V1.';
            END IF;
        END $$;
        """
    )
    op.create_table(
        "sql_analysis_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_sql", sa.Text(), nullable=False),
        sa.Column("sql_type", sa.String(length=50)),
        sa.Column("summary", sa.Text()),
        sa.Column("involved_tables", postgresql.JSONB()),
        sa.Column("involved_columns", postgresql.JSONB()),
        sa.Column("join_relations", postgresql.JSONB()),
        sa.Column("where_conditions", postgresql.JSONB()),
        sa.Column("risk_level", sa.String(length=20)),
        sa.Column("risk_items", postgresql.JSONB()),
        sa.Column("analysis_result_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sql_analysis_record_created_at", "sql_analysis_record", ["created_at"])
    op.create_index("ix_sql_analysis_record_risk_level", "sql_analysis_record", ["risk_level"])

    op.create_table(
        "metadata_table",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("table_comment", sa.Text()),
        sa.Column("business_domain", sa.String(length=100)),
        sa.Column("owner", sa.String(length=100)),
        sa.Column("update_frequency", sa.String(length=50)),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_metadata_table_table_name", "metadata_table", ["table_name"])

    op.create_table(
        "metadata_column",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(length=255), nullable=False),
        sa.Column("column_name", sa.String(length=255), nullable=False),
        sa.Column("data_type", sa.String(length=100)),
        sa.Column("column_comment", sa.Text()),
        sa.Column("business_desc", sa.Text()),
        sa.Column("example_value", sa.Text()),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_metadata_column_table_column", "metadata_column", ["table_name", "column_name"])

    op.create_table(
        "metric_definition",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("metric_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("formula", sa.Text()),
        sa.Column("business_desc", sa.Text()),
        sa.Column("source_tables", postgresql.JSONB()),
        sa.Column("source_columns", postgresql.JSONB()),
        sa.Column("dimension", sa.Text()),
        sa.Column("frequency", sa.String(length=50)),
        sa.Column("example_sql", sa.Text()),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_metric_definition_metric_code", "metric_definition", ["metric_code"])


def downgrade() -> None:
    op.drop_table("metric_definition")
    op.drop_table("metadata_column")
    op.drop_table("metadata_table")
    op.drop_table("sql_analysis_record")
