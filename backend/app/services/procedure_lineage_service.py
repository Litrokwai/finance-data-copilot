from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Iterable

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.models.metadata_table import MetadataTable
from app.models.procedure_lineage_edge import ProcedureLineageEdge
from app.models.procedure_lineage_record import ProcedureLineageRecord


READ_PATTERN = re.compile(r"\b(?:FROM|JOIN|APPLY)\s+([#@\[\]\w.]+)", re.IGNORECASE)
INSERT_PATTERN = re.compile(r"\bINSERT\s+(?:INTO\s+)?([#@\[\]\w.]+)", re.IGNORECASE)
UPDATE_PATTERN = re.compile(r"\bUPDATE\s+([#@\[\]\w.]+)", re.IGNORECASE)
MERGE_PATTERN = re.compile(r"\bMERGE\s+(?:INTO\s+)?([#@\[\]\w.]+)", re.IGNORECASE)
DELETE_PATTERN = re.compile(r"\bDELETE\s+(?:FROM\s+)?([#@\[\]\w.]+)", re.IGNORECASE)
SELECT_INTO_PATTERN = re.compile(r"\bINTO\s+([#@\[\]\w.]+)\s+FROM\b", re.IGNORECASE)
TRUNCATE_PATTERN = re.compile(r"\bTRUNCATE\s+TABLE\s+([#@\[\]\w.]+)", re.IGNORECASE)
DYNAMIC_SQL_PATTERN = re.compile(r"\b(?:sp_executesql|EXEC(?:UTE)?\s*\(|EXEC(?:UTE)?\s+@)", re.IGNORECASE)

NOISE_TOKENS = {
    "NOLOCK",
    "WITH",
    "SELECT",
    "VALUES",
    "OPENQUERY",
    "OPENROWSET",
    "INSERTED",
    "DELETED",
}


def parse_procedure_lineage(definition: str, procedure_name: str) -> dict:
    cleaned = _strip_comments(definition)
    statements = _split_statements(cleaned)
    dynamic_sql_detected = bool(DYNAMIC_SQL_PATTERN.search(cleaned))

    read_tables: set[str] = set()
    write_tables: set[str] = set()
    temp_tables: set[str] = set()
    structured_edges: list[dict] = []

    for index, statement in enumerate(statements, start=1):
        statement_type = _statement_type(statement)
        statement_reads = _extract_tables(statement, [READ_PATTERN])
        statement_writes = _extract_tables(
            statement,
            [INSERT_PATTERN, UPDATE_PATTERN, MERGE_PATTERN, DELETE_PATTERN, SELECT_INTO_PATTERN, TRUNCATE_PATTERN],
        )

        temp_tables.update({table for table in statement_reads | statement_writes if _is_temp_table(table)})
        read_tables.update({table for table in statement_reads if not _is_temp_table(table)})
        write_tables.update({table for table in statement_writes if not _is_temp_table(table)})

        for table in sorted(statement_reads):
            structured_edges.append(
                _edge(
                    source_object=table,
                    target_object=procedure_name,
                    relation_type="READ",
                    source_kind=_object_kind(table),
                    target_kind="procedure",
                    statement_index=index,
                    statement_type=statement_type,
                    statement_snippet=_snippet(statement),
                    confidence=0.85 if not _is_temp_table(table) else 0.75,
                )
            )
        for table in sorted(statement_writes):
            structured_edges.append(
                _edge(
                    source_object=procedure_name,
                    target_object=table,
                    relation_type="WRITE",
                    source_kind="procedure",
                    target_kind=_object_kind(table),
                    statement_index=index,
                    statement_type=statement_type,
                    statement_snippet=_snippet(statement),
                    confidence=0.85 if not _is_temp_table(table) else 0.75,
                )
            )
        for source in sorted(statement_reads):
            for target in sorted(statement_writes):
                if source == target:
                    continue
                structured_edges.append(
                    _edge(
                        source_object=source,
                        target_object=target,
                        relation_type="TABLE_FLOW",
                        source_kind=_object_kind(source),
                        target_kind=_object_kind(target),
                        statement_index=index,
                        statement_type=statement_type,
                        statement_snippet=_snippet(statement),
                        confidence=0.65 if _is_temp_table(source) or _is_temp_table(target) else 0.7,
                    )
                )

    legacy_edges = [
        {"source": table, "target": procedure_name, "relation": "READ"} for table in sorted(read_tables)
    ] + [
        {"source": procedure_name, "target": table, "relation": "WRITE"} for table in sorted(write_tables)
    ]
    parse_status = "REVIEW" if dynamic_sql_detected else "SUCCESS"
    parse_message = "检测到动态 SQL，血缘结果需要人工复核。" if dynamic_sql_detected else None

    return {
        "definition_hash": hashlib.sha256(definition.encode("utf-8")).hexdigest(),
        "read_tables": sorted(read_tables),
        "write_tables": sorted(write_tables),
        "temp_tables": sorted(temp_tables),
        "lineage_edges": legacy_edges,
        "structured_edges": _dedupe_edges(structured_edges),
        "statement_count": len(statements),
        "parse_status": parse_status,
        "parse_message": parse_message,
    }


def upsert_procedure_lineage(
    db: Session,
    *,
    procedure_name: str,
    procedure_schema: str | None,
    database_name: str | None,
    source_system: str | None,
    definition: str,
) -> ProcedureLineageRecord:
    parsed = parse_procedure_lineage(definition, procedure_name)
    record = db.query(ProcedureLineageRecord).filter(ProcedureLineageRecord.procedure_name == procedure_name).one_or_none()
    if record is None:
        record = ProcedureLineageRecord(procedure_name=procedure_name)
        db.add(record)
        db.flush()

    record.procedure_schema = procedure_schema
    record.database_name = database_name
    record.source_system = source_system
    record.definition_hash = parsed["definition_hash"]
    record.read_tables = parsed["read_tables"]
    record.write_tables = parsed["write_tables"]
    record.temp_tables = parsed["temp_tables"]
    record.lineage_edges = parsed["lineage_edges"]
    record.statement_count = parsed["statement_count"]
    record.parse_status = parsed["parse_status"]
    record.parse_message = parsed["parse_message"]
    record.synced_at = datetime.now().astimezone()
    db.flush()

    db.query(ProcedureLineageEdge).filter(ProcedureLineageEdge.procedure_id == record.id).delete()
    for item in parsed["structured_edges"]:
        db.add(
            ProcedureLineageEdge(
                procedure_id=record.id,
                procedure_name=procedure_name,
                source_object=item["source_object"][:512],
                target_object=item["target_object"][:512],
                relation_type=item["relation_type"],
                source_kind=item["source_kind"],
                target_kind=item["target_kind"],
                statement_index=item["statement_index"],
                statement_type=item["statement_type"],
                confidence=item["confidence"],
                statement_snippet=item["statement_snippet"],
            )
        )
    return record


def get_lineage_summary(db: Session) -> dict:
    total_procedures = db.query(func.count(ProcedureLineageRecord.id)).scalar() or 0
    total_edges = db.query(func.count(ProcedureLineageEdge.id)).scalar() or 0
    review_count = (
        db.query(func.count(ProcedureLineageRecord.id))
        .filter(ProcedureLineageRecord.parse_status == "REVIEW")
        .scalar()
        or 0
    )
    read_tables = {
        _canonical_table_key(row[0])
        for row in db.query(ProcedureLineageEdge.source_object)
        .filter(ProcedureLineageEdge.relation_type == "READ", ProcedureLineageEdge.source_kind == "table")
        .distinct()
        .all()
        if row[0]
    }
    write_tables = {
        _canonical_table_key(row[0])
        for row in db.query(ProcedureLineageEdge.target_object)
        .filter(ProcedureLineageEdge.relation_type == "WRITE", ProcedureLineageEdge.target_kind == "table")
        .distinct()
        .all()
        if row[0]
    }
    latest_sync_time = db.query(func.max(ProcedureLineageRecord.synced_at)).scalar()
    return {
        "total_procedures": total_procedures,
        "total_read_tables": len(read_tables),
        "total_write_tables": len(write_tables),
        "total_edges": total_edges,
        "review_count": review_count,
        "latest_sync_time": latest_sync_time.isoformat() if latest_sync_time else None,
    }


def list_procedure_lineage(
    db: Session,
    keyword: str | None = None,
    parse_status: str | None = None,
) -> list[dict]:
    query = db.query(ProcedureLineageRecord)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                ProcedureLineageRecord.procedure_name.ilike(pattern),
                cast(ProcedureLineageRecord.read_tables, String).ilike(pattern),
                cast(ProcedureLineageRecord.write_tables, String).ilike(pattern),
            )
        )
    if parse_status and parse_status.strip():
        query = query.filter(ProcedureLineageRecord.parse_status == parse_status.strip().upper())
    records = query.order_by(ProcedureLineageRecord.synced_at.desc(), ProcedureLineageRecord.procedure_name.asc()).all()
    return [_build_item(db, record) for record in records]


def get_procedure_lineage_detail(db: Session, record_id: int) -> dict | None:
    record = db.get(ProcedureLineageRecord, record_id)
    if record is None:
        return None
    edges = (
        db.query(ProcedureLineageEdge)
        .filter(ProcedureLineageEdge.procedure_id == record.id)
        .order_by(ProcedureLineageEdge.statement_index.asc().nulls_last(), ProcedureLineageEdge.relation_type.asc())
        .all()
    )
    return {
        **_build_item(db, record),
        "read_tables": record.read_tables or [],
        "write_tables": record.write_tables or [],
        "temp_tables": record.temp_tables or [],
        "lineage_edges": record.lineage_edges or [],
        "structured_edges": [_build_edge(edge) for edge in edges],
    }


def get_procedure_lineage_graph(
    db: Session,
    keyword: str | None = None,
    max_procedures: int = 80,
    parse_status: str | None = None,
) -> dict:
    query = db.query(ProcedureLineageRecord)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                ProcedureLineageRecord.procedure_name.ilike(pattern),
                cast(ProcedureLineageRecord.read_tables, String).ilike(pattern),
                cast(ProcedureLineageRecord.write_tables, String).ilike(pattern),
            )
        )
    if parse_status and parse_status.strip():
        query = query.filter(ProcedureLineageRecord.parse_status == parse_status.strip().upper())
    records = query.order_by(ProcedureLineageRecord.synced_at.desc(), ProcedureLineageRecord.procedure_name.asc()).limit(max_procedures).all()
    record_ids = [record.id for record in records]
    if not record_ids:
        return {"nodes": [], "edges": []}

    edges = (
        db.query(ProcedureLineageEdge)
        .filter(ProcedureLineageEdge.procedure_id.in_(record_ids), ProcedureLineageEdge.relation_type.in_(["READ", "WRITE"]))
        .all()
    )
    node_map: dict[str, dict] = {}
    graph_edges = []
    for record in records:
        proc_key = f"procedure:{record.procedure_name}"
        node_map[proc_key] = {
            "id": proc_key,
            "name": record.procedure_name,
            "category": "procedure",
            "symbolSize": 54,
            "value": record.statement_count,
        }
    for edge in edges:
        source_key = _node_key(edge.source_kind, edge.source_object)
        target_key = _node_key(edge.target_kind, edge.target_object)
        node_map.setdefault(
            source_key,
            {
                "id": source_key,
                "name": _short_table_name(edge.source_object),
                "full_name": edge.source_object,
                "category": _graph_category(edge.source_kind, edge.relation_type, "source"),
                "symbolSize": 34 if edge.source_kind != "procedure" else 54,
            },
        )
        node_map.setdefault(
            target_key,
            {
                "id": target_key,
                "name": _short_table_name(edge.target_object),
                "full_name": edge.target_object,
                "category": _graph_category(edge.target_kind, edge.relation_type, "target"),
                "symbolSize": 38 if edge.target_kind != "procedure" else 54,
            },
        )
        graph_edges.append({"source": source_key, "target": target_key, "relation": edge.relation_type})

    return {"nodes": list(node_map.values()), "edges": graph_edges}


def list_lineage_tables(db: Session, keyword: str | None = None, limit: int = 200) -> list[dict]:
    read_rows = _table_usage_rows(db, "READ", keyword)
    write_rows = _table_usage_rows(db, "WRITE", keyword)
    known_tables = _known_table_names(db)
    table_map: dict[str, dict] = {}

    for table_name, procedure_names, edge_count in read_rows:
        if not _is_known_or_qualified_table(table_name, known_tables):
            continue
        key = _canonical_table_key(table_name)
        item = table_map.setdefault(key, _empty_table_usage(table_name))
        _merge_table_usage(item, table_name, procedure_names, edge_count, "read")
    for table_name, procedure_names, edge_count in write_rows:
        if not _is_known_or_qualified_table(table_name, known_tables):
            continue
        key = _canonical_table_key(table_name)
        item = table_map.setdefault(key, _empty_table_usage(table_name))
        _merge_table_usage(item, table_name, procedure_names, edge_count, "write")

    rows = list(table_map.values())
    for item in rows:
        item["read_by_count"] = len(item.pop("_read_procedure_names"))
        item["write_by_count"] = len(item.pop("_write_procedure_names"))
        item["edge_count"] = item["read_edge_count"] + item["write_edge_count"]
        item.pop("_display_weight")
    rows.sort(key=lambda item: (item["read_by_count"] + item["write_by_count"], item["edge_count"]), reverse=True)
    return rows[:limit]


def get_table_impact(db: Session, table_name: str) -> dict:
    table_name = table_name.strip()
    read_edges = (
        db.query(ProcedureLineageEdge)
        .filter(
            ProcedureLineageEdge.relation_type == "READ",
            ProcedureLineageEdge.source_kind == "table",
            _table_match_filter(ProcedureLineageEdge.source_object, table_name),
        )
        .order_by(ProcedureLineageEdge.procedure_name.asc(), ProcedureLineageEdge.statement_index.asc().nulls_last())
        .all()
    )
    write_edges = (
        db.query(ProcedureLineageEdge)
        .filter(
            ProcedureLineageEdge.relation_type == "WRITE",
            ProcedureLineageEdge.target_kind == "table",
            _table_match_filter(ProcedureLineageEdge.target_object, table_name),
        )
        .order_by(ProcedureLineageEdge.procedure_name.asc(), ProcedureLineageEdge.statement_index.asc().nulls_last())
        .all()
    )
    table_flow_edges = (
        db.query(ProcedureLineageEdge)
        .filter(
            ProcedureLineageEdge.relation_type == "TABLE_FLOW",
            or_(
                _table_match_filter(ProcedureLineageEdge.source_object, table_name),
                _table_match_filter(ProcedureLineageEdge.target_object, table_name),
            ),
        )
        .order_by(ProcedureLineageEdge.procedure_name.asc(), ProcedureLineageEdge.statement_index.asc().nulls_last())
        .limit(500)
        .all()
    )

    matched_name = _first_table_name(read_edges, write_edges, table_flow_edges) or table_name
    return {
        "table_name": matched_name,
        "read_by_procedures": _procedure_refs(read_edges),
        "write_by_procedures": _procedure_refs(write_edges),
        "read_edges": [_build_edge(edge) for edge in read_edges[:500]],
        "write_edges": [_build_edge(edge) for edge in write_edges[:500]],
        "table_flow_edges": [_build_edge(edge) for edge in table_flow_edges],
    }


def _build_item(db: Session, record: ProcedureLineageRecord) -> dict:
    edge_count = (
        db.query(func.count(ProcedureLineageEdge.id))
        .filter(ProcedureLineageEdge.procedure_id == record.id)
        .scalar()
        or 0
    )
    table_flow_count = (
        db.query(func.count(ProcedureLineageEdge.id))
        .filter(ProcedureLineageEdge.procedure_id == record.id, ProcedureLineageEdge.relation_type == "TABLE_FLOW")
        .scalar()
        or 0
    )
    return {
        "id": record.id,
        "procedure_name": record.procedure_name,
        "procedure_schema": record.procedure_schema,
        "database_name": record.database_name,
        "source_system": record.source_system,
        "read_table_count": len(record.read_tables or []),
        "write_table_count": len(record.write_tables or []),
        "temp_table_count": len(record.temp_tables or []),
        "edge_count": edge_count,
        "table_flow_count": table_flow_count,
        "statement_count": record.statement_count,
        "parse_status": record.parse_status,
        "parse_message": record.parse_message,
        "synced_at": record.synced_at.isoformat() if record.synced_at else None,
    }


def _build_edge(edge: ProcedureLineageEdge) -> dict:
    return {
        "id": edge.id,
        "source_object": edge.source_object,
        "target_object": edge.target_object,
        "relation_type": edge.relation_type,
        "source_kind": edge.source_kind,
        "target_kind": edge.target_kind,
        "statement_index": edge.statement_index,
        "statement_type": edge.statement_type,
        "confidence": edge.confidence,
        "statement_snippet": edge.statement_snippet,
    }


def _table_usage_rows(db: Session, relation_type: str, keyword: str | None = None) -> list[tuple[str, set[str], int]]:
    object_column = (
        ProcedureLineageEdge.source_object if relation_type == "READ" else ProcedureLineageEdge.target_object
    )
    kind_column = ProcedureLineageEdge.source_kind if relation_type == "READ" else ProcedureLineageEdge.target_kind
    query = (
        db.query(
            object_column.label("table_name"),
            ProcedureLineageEdge.procedure_name.label("procedure_name"),
            func.count(ProcedureLineageEdge.id).label("edge_count"),
        )
        .filter(ProcedureLineageEdge.relation_type == relation_type, kind_column == "table")
        .group_by(object_column, ProcedureLineageEdge.procedure_name)
    )
    if keyword and keyword.strip():
        query = query.filter(object_column.ilike(f"%{keyword.strip()}%"))
    return [(row.table_name, {row.procedure_name}, row.edge_count or 0) for row in query.all()]


def _empty_table_usage(table_name: str) -> dict:
    return {
        "table_name": table_name,
        "read_by_count": 0,
        "write_by_count": 0,
        "read_edge_count": 0,
        "write_edge_count": 0,
        "edge_count": 0,
        "_read_procedure_names": set(),
        "_write_procedure_names": set(),
        "_display_weight": (0, 0, 0),
    }


def _merge_table_usage(
    item: dict,
    table_name: str,
    procedure_names: set[str],
    edge_count: int,
    direction: str,
) -> None:
    if direction == "read":
        item["_read_procedure_names"].update(procedure_names)
        item["read_edge_count"] += edge_count
    else:
        item["_write_procedure_names"].update(procedure_names)
        item["write_edge_count"] += edge_count

    display_weight = _table_display_weight(table_name, edge_count)
    if display_weight > item["_display_weight"]:
        item["table_name"] = table_name
        item["_display_weight"] = display_weight


def _table_display_weight(table_name: str, edge_count: int) -> tuple[int, int, int]:
    parts = [part for part in table_name.split(".") if part]
    uppercase_score = sum(1 for char in table_name if char.isupper())
    return (edge_count, len(parts), uppercase_score)


def _table_match_filter(column, table_name: str):
    normalized = table_name.strip().lower()
    return or_(func.lower(column) == normalized, func.lower(column).like(f"%.{normalized}"))


def _canonical_table_key(table_name: str) -> str:
    return table_name.strip().lower()


def _first_table_name(*edge_groups: list[ProcedureLineageEdge]) -> str | None:
    for edges in edge_groups:
        for edge in edges:
            if edge.relation_type == "READ":
                return edge.source_object
            if edge.relation_type == "WRITE":
                return edge.target_object
            if edge.source_kind == "table":
                return edge.source_object
            if edge.target_kind == "table":
                return edge.target_object
    return None


def _procedure_refs(edges: list[ProcedureLineageEdge]) -> list[dict]:
    seen = set()
    result = []
    for edge in edges:
        if edge.procedure_name in seen:
            continue
        seen.add(edge.procedure_name)
        result.append(
            {
                "procedure_id": edge.procedure_id,
                "procedure_name": edge.procedure_name,
            }
        )
    return result


def _known_table_names(db: Session) -> set[str]:
    names = {row[0] for row in db.query(MetadataTable.table_name).all() if row[0]}
    normalized = set()
    for name in names:
        lower_name = name.lower()
        normalized.add(lower_name)
        normalized.add(_short_table_name(lower_name))
        parts = [part for part in lower_name.split(".") if part]
        if len(parts) >= 2:
            normalized.add(".".join(parts[-2:]))
    return normalized


def _is_known_or_qualified_table(value: str, known_tables: set[str]) -> bool:
    lower_value = value.lower()
    if lower_value in known_tables or _short_table_name(lower_value) in known_tables:
        return True
    parts = [part for part in lower_value.split(".") if part]
    if len(parts) >= 3:
        return True
    return len(parts) >= 2 and len(parts[-1]) > 2


def _split_statements(sql: str) -> list[str]:
    raw_statements = re.split(r";|\bGO\b", sql, flags=re.IGNORECASE)
    statements = [item.strip() for item in raw_statements if item.strip()]
    if len(statements) <= 1:
        statements = [line.strip() for line in sql.splitlines() if re.search(r"\b(?:SELECT|INSERT|UPDATE|DELETE|MERGE|TRUNCATE)\b", line, re.IGNORECASE)]
    return statements or [sql.strip()]


def _statement_type(statement: str) -> str:
    match = re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|MERGE|TRUNCATE|CREATE|ALTER)\b", statement, re.IGNORECASE)
    return match.group(1).upper() if match else "UNKNOWN"


def _extract_tables(sql: str, patterns: Iterable[re.Pattern[str]]) -> set[str]:
    tables: set[str] = set()
    for pattern in patterns:
        for match in pattern.findall(sql):
            table = _normalize_identifier(match)
            if _is_real_table_ref(table):
                tables.add(table)
    return tables


def _normalize_identifier(value: str) -> str:
    value = value.strip().rstrip(",);")
    value = re.split(r"\s+", value)[0]
    value = value.replace("[", "").replace("]", "")
    while ".." in value:
        value = value.replace("..", ".")
    return value.strip()


def _is_real_table_ref(value: str) -> bool:
    if not value or value.startswith("@"):
        return False
    upper = value.upper().split(".")[-1]
    return upper not in NOISE_TOKENS


def _is_temp_table(value: str) -> bool:
    return value.startswith("#")


def _object_kind(value: str) -> str:
    return "temp_table" if _is_temp_table(value) else "table"


def _edge(
    *,
    source_object: str,
    target_object: str,
    relation_type: str,
    source_kind: str,
    target_kind: str,
    statement_index: int,
    statement_type: str,
    statement_snippet: str,
    confidence: float,
) -> dict:
    return {
        "source_object": source_object,
        "target_object": target_object,
        "relation_type": relation_type,
        "source_kind": source_kind,
        "target_kind": target_kind,
        "statement_index": statement_index,
        "statement_type": statement_type,
        "statement_snippet": statement_snippet,
        "confidence": confidence,
    }


def _dedupe_edges(edges: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for edge in edges:
        key = (
            edge["source_object"],
            edge["target_object"],
            edge["relation_type"],
            edge["statement_index"],
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(edge)
    return result


def _node_key(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _graph_category(kind: str, relation_type: str, direction: str) -> str:
    if kind == "procedure":
        return "procedure"
    if kind == "temp_table":
        return "temp_table"
    if relation_type == "WRITE" and direction == "target":
        return "write_table"
    return "read_table"


def _short_table_name(value: str) -> str:
    parts = [part for part in value.split(".") if part]
    return ".".join(parts[-2:]) if len(parts) >= 2 else value


def _snippet(statement: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", statement).strip()[:limit]


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    return sql
