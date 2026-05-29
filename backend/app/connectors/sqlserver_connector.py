from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyodbc


@dataclass(frozen=True)
class SqlServerConfig:
    host: str
    fallback_hosts: list[str]
    port: int
    fallback_ports: list[int]
    database: str
    user: str
    password: str
    odbc_driver: str = "ODBC Driver 17 for SQL Server"
    connect_timeout_sec: int = 10

    @property
    def hosts(self) -> list[str]:
        return [self.host, *[host for host in self.fallback_hosts if host != self.host]]

    @property
    def ports(self) -> list[int]:
        return [self.port, *[port for port in self.fallback_ports if port != self.port]]


def load_sqlserver_config(config_path: str | Path) -> SqlServerConfig:
    raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
    db = raw["database"]
    return SqlServerConfig(
        host=db["host"],
        fallback_hosts=db.get("fallback_hosts", []),
        port=int(db.get("port", 1433)),
        fallback_ports=[int(port) for port in db.get("fallback_ports", [])],
        database=db["database"],
        user=db["user"],
        password=db["password"],
        odbc_driver=db.get("odbc_driver", "ODBC Driver 17 for SQL Server"),
        connect_timeout_sec=int(db.get("connect_timeout_sec", 10)),
    )


def build_connection_string(config: SqlServerConfig, host: str, port: int) -> str:
    return (
        f"DRIVER={{{config.odbc_driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE={config.database};"
        f"UID={config.user};PWD={config.password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    )


@contextmanager
def connect_sqlserver(config: SqlServerConfig) -> Iterator[tuple[pyodbc.Connection, str, int]]:
    errors: list[str] = []
    for host in config.hosts:
        for port in config.ports:
            try:
                conn = pyodbc.connect(
                    build_connection_string(config, host, port),
                    timeout=config.connect_timeout_sec,
                )
                yield conn, host, port
                conn.close()
                return
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{host}:{port} -> {exc}")
    raise RuntimeError("All SQL Server connection attempts failed:\n" + "\n".join(errors))


def fetch_connection_summary(config_path: str | Path) -> dict[str, Any]:
    config = load_sqlserver_config(config_path)
    with connect_sqlserver(config) as (conn, host, port):
        cur = conn.cursor()
        cur.execute("select db_name() as database_name, system_user as login_name")
        database_name, login_name = cur.fetchone()
        cur.execute("select count(*) from information_schema.tables where table_type = 'BASE TABLE'")
        table_count = cur.fetchone()[0]
        cur.execute(
            """
            select top 10 table_schema, table_name
            from information_schema.tables
            where table_type = 'BASE TABLE'
            order by table_schema, table_name
            """
        )
        sample_tables = [{"schema": row[0], "table": row[1]} for row in cur.fetchall()]
        cur.close()
        return {
            "host": host,
            "port": port,
            "database": database_name,
            "login": login_name,
            "table_count": table_count,
            "sample_tables": sample_tables,
        }
