from __future__ import annotations

import argparse
from pathlib import Path

from app.connectors.sqlserver_connector import fetch_connection_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Check company SQL Server connectivity.")
    parser.add_argument(
        "--config",
        default="../Annual_Strategy_Metrics/db_config.json",
        help="Path to an existing SQL Server config JSON.",
    )
    args = parser.parse_args()

    summary = fetch_connection_summary(Path(args.config))
    print("SQL Server connection OK")
    print(f"Host: {summary['host']}:{summary['port']}")
    print(f"Database: {summary['database']}")
    print(f"Login: {summary['login']}")
    print(f"Base table count: {summary['table_count']}")
    print("Sample tables:")
    for table in summary["sample_tables"]:
        print(f"  - {table['schema']}.{table['table']}")


if __name__ == "__main__":
    main()
