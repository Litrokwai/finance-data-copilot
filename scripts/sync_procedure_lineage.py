from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.connectors.sqlserver_connector import connect_sqlserver, load_sqlserver_config  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.services.procedure_lineage_service import upsert_procedure_lineage  # noqa: E402


DEFAULT_CONFIG = "../Annual_Strategy_Metrics/db_config.json"
SOURCE_DATABASE = "Howgow"
SOURCE_SYSTEM = "howgow_linked_server"


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def openquery_sql(remote_sql: str) -> str:
    escaped_sql = remote_sql.replace("'", "''")
    return f"SELECT * FROM OPENQUERY([howgow_srv], '{escaped_sql}')"


def fetch_procedure_count(cursor) -> int:
    cursor.execute(
        openquery_sql(
            f"""
            SELECT COUNT(*) AS procedure_count
            FROM [{SOURCE_DATABASE}].sys.procedures p
            JOIN [{SOURCE_DATABASE}].sys.sql_modules m ON p.object_id = m.object_id
            WHERE m.definition IS NOT NULL
            """
        )
    )
    return int(cursor.fetchone().procedure_count)


def fetch_named_procedure_definitions(cursor, procedure_names: list[str]) -> list[dict[str, Any]]:
    if not procedure_names:
        return []
    names = ", ".join(sql_literal(name) for name in procedure_names)
    remote_sql = f"""
        SELECT
            p.object_id,
            s.name AS procedure_schema,
            p.name AS procedure_name,
            m.definition AS definition
        FROM [{SOURCE_DATABASE}].sys.procedures p
        JOIN [{SOURCE_DATABASE}].sys.schemas s ON p.schema_id = s.schema_id
        JOIN [{SOURCE_DATABASE}].sys.sql_modules m ON p.object_id = m.object_id
        WHERE m.definition IS NOT NULL
          AND p.name IN ({names})
        ORDER BY p.object_id
    """
    cursor.execute(openquery_sql(remote_sql))
    return [_row_to_definition(row) for row in cursor.fetchall()]


def fetch_procedure_batch(cursor, last_object_id: int, batch_size: int) -> list[dict[str, Any]]:
    remote_sql = f"""
        SELECT TOP {int(batch_size)}
            p.object_id,
            s.name AS procedure_schema,
            p.name AS procedure_name,
            m.definition AS definition
        FROM [{SOURCE_DATABASE}].sys.procedures p
        JOIN [{SOURCE_DATABASE}].sys.schemas s ON p.schema_id = s.schema_id
        JOIN [{SOURCE_DATABASE}].sys.sql_modules m ON p.object_id = m.object_id
        WHERE m.definition IS NOT NULL
          AND p.object_id > {int(last_object_id)}
        ORDER BY p.object_id
    """
    cursor.execute(openquery_sql(remote_sql))
    return [_row_to_definition(row) for row in cursor.fetchall()]


def iter_all_procedure_definitions(cursor, batch_size: int, limit: int | None = None):
    last_object_id = 0
    emitted = 0
    while True:
        rows = fetch_procedure_batch(cursor, last_object_id, batch_size)
        if not rows:
            break
        if limit is not None:
            rows = rows[: max(limit - emitted, 0)]
        if not rows:
            break
        yield rows
        emitted += len(rows)
        last_object_id = max(int(row["object_id"]) for row in rows)
        if limit is not None and emitted >= limit:
            break


def _row_to_definition(row) -> dict[str, Any]:
    return {
        "object_id": int(row.object_id),
        "procedure_schema": row.procedure_schema,
        "procedure_name": row.procedure_name,
        "database_name": SOURCE_DATABASE,
        "source_system": SOURCE_SYSTEM,
        "definition": row.definition,
    }


def sync_rows(rows: list[dict[str, Any]], dry_run: bool) -> tuple[int, int]:
    synced = 0
    review = 0
    if dry_run:
        from app.services.procedure_lineage_service import parse_procedure_lineage

        for row in rows:
            parsed = parse_procedure_lineage(row["definition"], row["procedure_name"])
            synced += 1
            review += 1 if parsed["parse_status"] == "REVIEW" else 0
        return synced, review

    with SessionLocal() as db:
        for row in rows:
            record = upsert_procedure_lineage(
                db,
                procedure_name=row["procedure_name"],
                procedure_schema=row["procedure_schema"],
                database_name=row["database_name"],
                source_system=row["source_system"],
                definition=row["definition"],
            )
            synced += 1
            review += 1 if record.parse_status == "REVIEW" else 0
        db.commit()
    return synced, review


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync stored procedure metadata lineage into local PostgreSQL.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to SQL Server config JSON.")
    parser.add_argument("--procedure", action="append", dest="procedures", help="Procedure name to sync. Can be repeated.")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for full sync.")
    parser.add_argument("--limit", type=int, default=0, help="Limit full sync rows for verification.")
    parser.add_argument("--dry-run", action="store_true", help="Only parse and summarize; do not write PostgreSQL.")
    args = parser.parse_args()

    config = load_sqlserver_config(PROJECT_ROOT / args.config)
    total_synced = 0
    total_review = 0
    with connect_sqlserver(config) as (conn, _, _):
        cursor = conn.cursor()
        if args.procedures:
            rows = fetch_named_procedure_definitions(cursor, args.procedures)
            synced, review = sync_rows(rows, args.dry_run)
            missing = sorted(set(args.procedures) - {row["procedure_name"] for row in rows})
            print({"mode": "named", "synced": synced, "review": review, "missing": missing, "dry_run": args.dry_run})
            return

        source_count = fetch_procedure_count(cursor)
        limit = args.limit if args.limit > 0 else None
        for rows in iter_all_procedure_definitions(cursor, args.batch_size, limit):
            synced, review = sync_rows(rows, args.dry_run)
            total_synced += synced
            total_review += review
            print({"batch_synced": synced, "total_synced": total_synced, "source_count": source_count, "dry_run": args.dry_run})

    print({"mode": "full", "source_count": source_count, "synced": total_synced, "review": total_review, "dry_run": args.dry_run})


if __name__ == "__main__":
    main()
