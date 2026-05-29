from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP_DSN = "host=127.0.0.1 port=5432 dbname=finance_data_copilot user=finance_copilot password=finance_copilot"
DEFAULT_BASE_URL = "https://dict.investoday.net"
DEFAULT_ACCOUNT = "links"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def fetch_json(base_url: str, path: str, params: dict[str, Any], cookie: str, timeout: int = 30) -> Any:
    query = urlencode({key: value for key, value in params.items() if value not in (None, "")})
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Cookie": cookie,
        "Referer": f"{base_url.rstrip('/')}/wap/view/index.html?account={DEFAULT_ACCOUNT}",
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
    }
    try:
        with urlopen(Request(url, headers=headers), timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Data dictionary API failed: HTTP {exc.code}; {text[:160]}") from exc

    if text.lstrip().startswith("<!DOCTYPE html") or "<html" in text[:200].lower():
        raise RuntimeError("Data dictionary API returned HTML. Please provide a valid browser session cookie.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Data dictionary API returned non-JSON content: {text[:160]}") from exc


def iter_table_refs(value: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("tableId") and value.get("tableName"):
            refs.append(value)
        for item in value.values():
            refs.extend(iter_table_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(iter_table_refs(item))
    return refs


def load_table_refs(base_url: str, account: str, cookie: str, table_names: list[str]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if table_names:
        for table_name in table_names:
            data = fetch_json(
                base_url,
                "/harvest/dict/serachDictTable",
                {"account": account, "srchtype": "1", "keyword": table_name},
                cookie,
            )
            refs.extend(iter_table_refs(data))
    else:
        data = fetch_json(base_url, "/harvest/dict/dictTable", {"account": account}, cookie)
        refs.extend(iter_table_refs(data))

    deduped: dict[str, dict[str, Any]] = {}
    expected = {name.lower() for name in table_names}
    for ref in refs:
        table_id = clean_text(ref.get("tableId"))
        table_name = clean_text(ref.get("tableName"))
        if not table_id or not table_name:
            continue
        if expected and table_name.lower() not in expected:
            continue
        deduped[table_id] = ref
    return list(deduped.values())


def find_local_table(cur, db_name: str, table_name: str) -> str | None:
    patterns = [
        f"%.{db_name}.dbo.{table_name}",
        f"%.dbo.{table_name}",
        f"%.{table_name}",
    ]
    for pattern in patterns:
        cur.execute(
            """
            select table_name
            from metadata_table
            where table_name ilike %s
            order by length(table_name) desc
            limit 1
            """,
            (pattern,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
    return None


def is_pk(value: Any) -> bool:
    text = clean_text(value)
    try:
        return int(text) > 0
    except ValueError:
        return text.lower() in {"true", "yes", "y", "是"}


def parse_nullable(value: Any) -> bool | None:
    text = clean_text(value).lower()
    if text in {"0", "false", "no", "n", "否"}:
        return False
    if text in {"1", "true", "yes", "y", "是"}:
        return True
    return None


def update_dictionary_detail(cur, table_name: str, detail: dict[str, Any], dry_run: bool) -> dict[str, int]:
    dict_cols = detail.get("dictCols") or []
    if not isinstance(dict_cols, list):
        return {"columns": 0, "primary_keys": 0, "remarks": 0}

    columns = 0
    primary_keys = 0
    remarks = 0
    if not dry_run:
        cur.execute("update metadata_column set is_primary_key = false where table_name = %s", (table_name,))

    for item in dict_cols:
        column_name = clean_text(item.get("colName"))
        if not column_name:
            continue
        column_comment = clean_text(item.get("colDescCN")) or clean_text(item.get("colDescCn"))
        business_desc = clean_text(item.get("rmrk"))
        nullable = parse_nullable(item.get("isNullable"))
        pk = is_pk(item.get("isPK"))
        if pk:
            primary_keys += 1
        if business_desc:
            remarks += 1
        if not dry_run:
            cur.execute(
                """
                update metadata_column
                set
                    column_comment = coalesce(nullif(%s, ''), column_comment),
                    business_desc = coalesce(nullif(%s, ''), business_desc),
                    is_primary_key = %s,
                    is_nullable = coalesce(%s, is_nullable),
                    updated_at = now()
                where table_name = %s
                  and lower(column_name) = lower(%s)
                """,
                (column_comment, business_desc, pk, nullable, table_name, column_name),
            )
        columns += 1
    return {"columns": columns, "primary_keys": primary_keys, "remarks": remarks}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync primary keys and sparse field remarks from the data dictionary web API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--account", default=DEFAULT_ACCOUNT)
    parser.add_argument("--cookie", default=os.getenv("DATA_DICT_COOKIE", ""), help="Browser session cookie for the data dictionary site.")
    parser.add_argument("--table", action="append", dest="tables", help="Table name to sync. Can be repeated.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of matched tables for testing.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--app-dsn", default=os.getenv("FINANCE_COPILOT_DSN", DEFAULT_APP_DSN))
    args = parser.parse_args()

    if not args.cookie:
        raise RuntimeError("DATA_DICT_COOKIE or --cookie is required because the data dictionary API depends on a browser session.")

    refs = load_table_refs(args.base_url, args.account, args.cookie, args.tables or [])
    if args.limit:
        refs = refs[: args.limit]

    synced_tables = 0
    synced_columns = 0
    synced_primary_keys = 0
    synced_remarks = 0
    missing_tables: list[str] = []

    with psycopg2.connect(args.app_dsn) as conn:
        with conn.cursor() as cur:
            for ref in refs:
                detail = fetch_json(args.base_url, "/harvest/dict/dictCol", {"tableId": ref["tableId"]}, args.cookie)
                dict_table = detail.get("dictTable") or {}
                db_name = clean_text(dict_table.get("dbName")) or clean_text(ref.get("dbName"))
                table_name = clean_text(dict_table.get("tableName")) or clean_text(ref.get("tableName"))
                local_table = find_local_table(cur, db_name, table_name)
                if not local_table:
                    missing_tables.append(table_name)
                    continue
                counts = update_dictionary_detail(cur, local_table, detail, args.dry_run)
                synced_tables += 1
                synced_columns += counts["columns"]
                synced_primary_keys += counts["primary_keys"]
                synced_remarks += counts["remarks"]
            if args.dry_run:
                conn.rollback()

    print(
        {
            "matched_tables": len(refs),
            "synced_tables": synced_tables,
            "synced_columns": synced_columns,
            "synced_primary_keys": synced_primary_keys,
            "synced_field_remarks": synced_remarks,
            "missing_tables": missing_tables[:20],
            "dry_run": args.dry_run,
        }
    )


if __name__ == "__main__":
    main()
