from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.connectors.sqlserver_connector import connect_sqlserver, load_sqlserver_config  # noqa: E402


DEFAULT_APP_DSN = "host=127.0.0.1 port=5432 dbname=finance_data_copilot user=finance_copilot password=finance_copilot"
DEFAULT_CONFIG = "../Annual_Strategy_Metrics/db_config.json"
DEFAULT_SYSTEM_KEY = "howgow_link"
OFFLINE_DOMAIN = "已下线表【禁止使用】"
STANDARD_COLUMN_DESCRIPTIONS = {
    "SEQ": "自增序号",
    "CREAT_TM": "创建时间",
    "UPDT_TM": "更新时间",
    "IS_VLD": "是否有效",
    "RMRK": "数据来源序号",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_json_list(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return [text]
    if isinstance(parsed, list):
        return [clean_text(item) for item in parsed if clean_text(item)]
    if isinstance(parsed, str):
        return [parsed]
    return [text]


def build_table_name(server_name: str, database_name: str, schema_name: str, table_name: str) -> str:
    parts = [server_name, database_name, schema_name, table_name]
    return ".".join(part for part in parts if clean_text(part))


def format_data_type(row: dict[str, Any]) -> str:
    data_type = clean_text(row.get("data_type"))
    char_length = row.get("char_length")
    precision = row.get("numeric_precision")
    scale = row.get("numeric_scale")
    if data_type.lower() in {"varchar", "nvarchar", "char", "nchar", "varbinary"} and char_length:
        if int(char_length) == -1:
            return f"{data_type}(max)"
        return f"{data_type}({char_length})"
    if data_type.lower() in {"numeric", "decimal"} and precision:
        return f"{data_type}({precision},{scale or 0})"
    return data_type


def is_sensitive(pii_level: Any) -> bool:
    level = clean_text(pii_level).lower()
    return bool(level and level not in {"none", "no", "n", "0", "无", "非敏感", "public"})


def parse_nullable(value: Any) -> bool | None:
    text = clean_text(value).lower()
    if text in {"yes", "y", "1", "true", "是", "可为空", "nullable"}:
        return True
    if text in {"no", "n", "0", "false", "否", "不可为空", "not null"}:
        return False
    return None


def fetch_source_metadata(config_path: Path, system_key: str, exclude_offline: bool) -> tuple[list[dict], list[dict], list[dict]]:
    config = load_sqlserver_config(config_path)
    with connect_sqlserver(config) as (conn, _, _):
        cur = conn.cursor()
        cur.execute(
            """
            select top 1 system_key, server_name, database_name
            from howgow.ai_platform.catalog_systems with(nolock)
            where system_key = ?
            """,
            system_key,
        )
        system = cur.fetchone()
        if not system:
            raise RuntimeError(f"System key not found in catalog_systems: {system_key}")
        server_name = clean_text(system.server_name)
        database_name = clean_text(system.database_name)

        offline_filter = "and isnull(business_domain, '') <> ?" if exclude_offline else ""
        params: list[Any] = [system_key]
        if exclude_offline:
            params.append(OFFLINE_DOMAIN)

        cur.execute(
            f"""
            select
                table_id, system_key, table_catalog, table_schema, table_name, table_type,
                row_count, business_name, business_domain, description, owner,
                data_level, refresh_frequency, collected_at, latest_creat_tm
            from howgow.ai_platform.catalog_tables with(nolock)
            where system_key = ?
              and isnull(table_name, '') <> ''
              {offline_filter}
            order by table_schema, table_name
            """,
            *params,
        )
        table_columns = [desc[0] for desc in cur.description]
        source_tables = []
        for row in cur.fetchall():
            item = dict(zip(table_columns, row))
            item["canonical_table_name"] = build_table_name(
                server_name,
                clean_text(item.get("table_catalog")) or database_name,
                clean_text(item.get("table_schema")),
                clean_text(item.get("table_name")),
            )
            source_tables.append(item)

        table_key_set = {
            (clean_text(item.get("system_key")), clean_text(item.get("table_schema")), clean_text(item.get("table_name")))
            for item in source_tables
        }
        cur.execute(
            """
            select
                column_id, system_key, table_schema, table_name, column_name,
                ordinal_position, data_type, char_length, numeric_precision, numeric_scale,
                is_nullable, column_default, business_name, description, pii_level,
                enum_values, collected_at
            from howgow.ai_platform.catalog_columns with(nolock)
            where system_key = ?
              and isnull(column_name, '') <> ''
            order by table_schema, table_name, ordinal_position
            """,
            system_key,
        )
        column_columns = [desc[0] for desc in cur.description]
        table_lookup = {
            (clean_text(item.get("system_key")), clean_text(item.get("table_schema")), clean_text(item.get("table_name"))): item
            for item in source_tables
        }
        source_columns = []
        for row in cur.fetchall():
            item = dict(zip(column_columns, row))
            key = (clean_text(item.get("system_key")), clean_text(item.get("table_schema")), clean_text(item.get("table_name")))
            if key not in table_key_set:
                continue
            table_item = table_lookup[key]
            item["canonical_table_name"] = table_item["canonical_table_name"]
            item["business_domain"] = table_item.get("business_domain")
            source_columns.append(item)

        cur.execute(
            """
            select
                metric_id, metric_code, metric_name, business_definition, calculation_logic,
                source_tables, dimensions, filters, update_frequency, owner, status,
                sql_example, tags, version_no, created_at, updated_at
            from howgow.ai_platform.metric_definitions with(nolock)
            order by metric_code
            """
        )
        metric_columns = [desc[0] for desc in cur.description]
        metrics = [dict(zip(metric_columns, row)) for row in cur.fetchall()]

        cur.execute(
            """
            select metric_code, upstream_type, upstream_name, relation_note
            from howgow.ai_platform.metric_lineage with(nolock)
            order by metric_code, upstream_type, upstream_name
            """
        )
        lineage: dict[str, dict[str, list[str]]] = {}
        for metric_code, upstream_type, upstream_name, _ in cur.fetchall():
            metric = lineage.setdefault(clean_text(metric_code), {"tables": [], "columns": []})
            upstream = clean_text(upstream_name)
            if not upstream:
                continue
            if clean_text(upstream_type).lower() == "column":
                metric["columns"].append(upstream)
            else:
                metric["tables"].append(upstream)
        cur.close()

    for metric in metrics:
        metric_lineage = lineage.get(clean_text(metric.get("metric_code")), {"tables": [], "columns": []})
        source_table_list = parse_json_list(metric.get("source_tables"))
        metric["source_table_list"] = sorted(set(source_table_list + metric_lineage["tables"]))
        metric["source_column_list"] = sorted(set(metric_lineage["columns"]))
    return source_tables, source_columns, metrics


def sync_to_postgres(app_dsn: str, tables: list[dict], columns: list[dict], metrics: list[dict]) -> dict[str, int]:
    table_names = [item["canonical_table_name"] for item in tables if len(item["canonical_table_name"]) <= 255]
    skipped_tables = len(tables) - len(table_names)

    with psycopg2.connect(app_dsn) as conn:
        with conn.cursor() as cur:
            if table_names:
                cur.execute("delete from metadata_column where table_name = any(%s)", (table_names,))

            inserted_tables = 0
            for item in tables:
                table_name = item["canonical_table_name"]
                if len(table_name) > 255:
                    continue
                table_comment = clean_text(item.get("business_name")) or clean_text(item.get("description"))
                business_domain = clean_text(item.get("business_domain")) or "好股库未分类"
                owner = clean_text(item.get("owner")) or "ai_platform"
                is_valid_table = business_domain != OFFLINE_DOMAIN
                cur.execute(
                    """
                    insert into metadata_table (
                        table_name, table_comment, business_domain, owner, update_frequency,
                        source_collected_at, latest_creat_tm, is_valid
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (table_name) do update set
                        table_comment = excluded.table_comment,
                        business_domain = excluded.business_domain,
                        owner = excluded.owner,
                        update_frequency = excluded.update_frequency,
                        source_collected_at = excluded.source_collected_at,
                        latest_creat_tm = excluded.latest_creat_tm,
                        is_valid = excluded.is_valid,
                        updated_at = now()
                    """,
                    (
                        table_name,
                        table_comment,
                        business_domain,
                        owner[:100],
                        clean_text(item.get("refresh_frequency")),
                        item.get("collected_at"),
                        item.get("latest_creat_tm"),
                        is_valid_table,
                    ),
                )
                inserted_tables += 1

            inserted_columns = 0
            for item in columns:
                table_name = item["canonical_table_name"]
                if len(table_name) > 255:
                    continue
                standard_desc = STANDARD_COLUMN_DESCRIPTIONS.get(clean_text(item.get("column_name")).upper(), "")
                if standard_desc:
                    column_comment = standard_desc
                    business_desc = standard_desc
                else:
                    column_comment = clean_text(item.get("business_name")) or clean_text(item.get("description"))
                    business_desc = clean_text(item.get("description")) or column_comment
                is_valid_column = clean_text(item.get("business_domain")) != OFFLINE_DOMAIN
                cur.execute(
                    """
                    insert into metadata_column (
                        table_name, column_name, ordinal_position, data_type, column_comment, business_desc,
                        example_value, is_primary_key, is_nullable, is_sensitive, is_valid
                    )
                    values (%s, %s, %s, %s, %s, %s, '', %s, %s, %s, %s)
                    """,
                    (
                        table_name,
                        clean_text(item.get("column_name")),
                        item.get("ordinal_position"),
                        format_data_type(item),
                        column_comment,
                        business_desc,
                        False,
                        parse_nullable(item.get("is_nullable")),
                        is_sensitive(item.get("pii_level")),
                        is_valid_column,
                    ),
                )
                inserted_columns += 1

            inserted_metrics = 0
            for item in metrics:
                metric_code = clean_text(item.get("metric_code"))
                if not metric_code:
                    continue
                status = clean_text(item.get("status")).lower()
                is_valid_metric = status not in {"inactive", "disabled", "deleted", "下线", "停用"}
                cur.execute(
                    """
                    insert into metric_definition (
                        metric_code, metric_name, formula, business_desc,
                        source_tables, source_columns, dimension, frequency,
                        example_sql, is_valid
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (metric_code) do update set
                        metric_name = excluded.metric_name,
                        formula = excluded.formula,
                        business_desc = excluded.business_desc,
                        source_tables = excluded.source_tables,
                        source_columns = excluded.source_columns,
                        dimension = excluded.dimension,
                        frequency = excluded.frequency,
                        example_sql = excluded.example_sql,
                        is_valid = excluded.is_valid,
                        updated_at = now()
                    """,
                    (
                        metric_code,
                        clean_text(item.get("metric_name")),
                        clean_text(item.get("calculation_logic")),
                        clean_text(item.get("business_definition")),
                        Json(item.get("source_table_list", [])),
                        Json(item.get("source_column_list", [])),
                        clean_text(item.get("dimensions")),
                        clean_text(item.get("update_frequency")),
                        clean_text(item.get("sql_example")),
                        is_valid_metric,
                    ),
                )
                inserted_metrics += 1

    return {
        "tables": inserted_tables,
        "columns": inserted_columns,
        "metrics": inserted_metrics,
        "skipped_long_table_names": skipped_tables,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Howgow ai_platform metadata into Finance Data Copilot.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to SQL Server config JSON.")
    parser.add_argument("--system-key", default=DEFAULT_SYSTEM_KEY, help="catalog_systems.system_key to sync.")
    parser.add_argument("--exclude-offline", action="store_true", help="Exclude offline/deprecated business domains.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and summarize without writing PostgreSQL.")
    parser.add_argument(
        "--app-dsn",
        default=os.getenv("FINANCE_COPILOT_DSN", DEFAULT_APP_DSN),
        help="PostgreSQL DSN for Finance Data Copilot application database.",
    )
    args = parser.parse_args()

    tables, columns, metrics = fetch_source_metadata(Path(args.config), args.system_key, args.exclude_offline)
    if args.dry_run:
        print({"tables": len(tables), "columns": len(columns), "metrics": len(metrics), "dry_run": True})
        return

    result = sync_to_postgres(args.app_dsn, tables, columns, metrics)
    print(result)


if __name__ == "__main__":
    main()
