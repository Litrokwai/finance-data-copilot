from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import String, case, cast, func, or_
from sqlalchemy.orm import Session

from app.models.metadata_column import MetadataColumn
from app.models.metadata_table import MetadataTable
from app.models.metric_definition import MetricDefinition
from app.models.procedure_lineage_edge import ProcedureLineageEdge


UNKNOWN_DOMAIN = "未分类"
UNCLASSIFIED_DOMAINS = {"", UNKNOWN_DOMAIN, "好股库未分类"}
STALE_SOURCE_DAYS = 730
TEST_OR_TEMP_TABLE_TOKENS = (
    "test",
    "tmp",
    "temp",
    "bak",
    "backup",
    "demo",
    "sample",
    "delete",
    "del_",
    "_del",
    "old",
)


def _domain_expr():
    return func.coalesce(func.nullif(MetadataTable.business_domain, ""), UNKNOWN_DOMAIN)


def _column_stats_subquery(db: Session):
    return (
        db.query(
            MetadataColumn.table_name.label("table_name"),
            func.count(MetadataColumn.id).label("column_count"),
            func.coalesce(
                func.sum(case((MetadataColumn.is_sensitive.is_(True), 1), else_=0)),
                0,
            ).label("sensitive_column_count"),
        )
        .group_by(MetadataColumn.table_name)
        .subquery()
    )


def get_metadata_summary(db: Session) -> dict:
    total_tables = db.query(func.count(MetadataTable.id)).scalar() or 0
    valid_tables = db.query(func.count(MetadataTable.id)).filter(MetadataTable.is_valid.is_(True)).scalar() or 0
    total_columns = db.query(func.count(MetadataColumn.id)).scalar() or 0
    valid_columns = db.query(func.count(MetadataColumn.id)).filter(MetadataColumn.is_valid.is_(True)).scalar() or 0
    sensitive_columns = db.query(func.count(MetadataColumn.id)).filter(MetadataColumn.is_sensitive.is_(True)).scalar() or 0
    total_metrics = db.query(func.count(MetricDefinition.id)).scalar() or 0
    valid_metrics = db.query(func.count(MetricDefinition.id)).filter(MetricDefinition.is_valid.is_(True)).scalar() or 0

    domain_rows = (
        db.query(_domain_expr().label("business_domain"), func.count(MetadataTable.id).label("table_count"))
        .group_by(_domain_expr())
        .order_by(func.count(MetadataTable.id).desc())
        .all()
    )

    column_stats = _column_stats_subquery(db)
    top_rows = (
        db.query(
            MetadataTable.table_name,
            _domain_expr().label("business_domain"),
            func.coalesce(column_stats.c.column_count, 0).label("column_count"),
        )
        .outerjoin(column_stats, MetadataTable.table_name == column_stats.c.table_name)
        .order_by(func.coalesce(column_stats.c.column_count, 0).desc(), MetadataTable.table_name.asc())
        .limit(10)
        .all()
    )

    return {
        "total_tables": total_tables,
        "valid_tables": valid_tables,
        "offline_tables": total_tables - valid_tables,
        "total_columns": total_columns,
        "valid_columns": valid_columns,
        "sensitive_columns": sensitive_columns,
        "total_metrics": total_metrics,
        "valid_metrics": valid_metrics,
        "domain_distribution": [
            {"business_domain": row.business_domain, "table_count": row.table_count} for row in domain_rows
        ],
        "top_table_columns": [
            {
                "table_name": row.table_name,
                "business_domain": row.business_domain,
                "column_count": row.column_count,
            }
            for row in top_rows
        ],
    }


def list_metadata_tables(
    db: Session,
    keyword: str | None,
    business_domain: str | None,
    is_valid: bool | None,
    page: int,
    page_size: int,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> dict:
    column_stats = _column_stats_subquery(db)
    query = db.query(
        MetadataTable,
        func.coalesce(column_stats.c.column_count, 0).label("column_count"),
        func.coalesce(column_stats.c.sensitive_column_count, 0).label("sensitive_column_count"),
    ).outerjoin(column_stats, MetadataTable.table_name == column_stats.c.table_name)

    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                MetadataTable.table_name.ilike(pattern),
                MetadataTable.table_comment.ilike(pattern),
                MetadataTable.business_domain.ilike(pattern),
                MetadataTable.owner.ilike(pattern),
            )
        )
    if business_domain:
        query = query.filter(_domain_expr() == business_domain)
    if is_valid is not None:
        query = query.filter(MetadataTable.is_valid.is_(is_valid))

    total = query.count()
    column_count_expr = func.coalesce(column_stats.c.column_count, 0)
    sensitive_count_expr = func.coalesce(column_stats.c.sensitive_column_count, 0)
    sort_columns = {
        "table_name": MetadataTable.table_name,
        "table_comment": MetadataTable.table_comment,
        "business_domain": _domain_expr(),
        "column_count": column_count_expr,
        "sensitive_column_count": sensitive_count_expr,
        "updated_at": MetadataTable.updated_at,
    }
    sort_expr = sort_columns.get(sort_by or "")
    if sort_expr is not None and sort_order in {"asc", "desc"}:
        primary_order = sort_expr.desc() if sort_order == "desc" else sort_expr.asc()
        query = query.order_by(primary_order, MetadataTable.table_name.asc())
    else:
        query = query.order_by(
            MetadataTable.is_valid.desc(),
            _domain_expr().asc(),
            column_count_expr.desc(),
            MetadataTable.table_name.asc(),
        )

    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_build_table_item(table, column_count, sensitive_column_count) for table, column_count, sensitive_column_count in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_metadata_table_detail(db: Session, table_id: int) -> dict | None:
    table = db.get(MetadataTable, table_id)
    if table is None:
        return None

    column_count = db.query(func.count(MetadataColumn.id)).filter(MetadataColumn.table_name == table.table_name).scalar() or 0
    sensitive_column_count = (
        db.query(func.count(MetadataColumn.id))
        .filter(MetadataColumn.table_name == table.table_name, MetadataColumn.is_sensitive.is_(True))
        .scalar()
        or 0
    )
    columns = (
        db.query(MetadataColumn)
        .filter(MetadataColumn.table_name == table.table_name)
        .order_by(MetadataColumn.ordinal_position.asc().nulls_last(), MetadataColumn.id.asc())
        .all()
    )
    metrics = (
        db.query(MetricDefinition)
        .filter(cast(MetricDefinition.source_tables, String).ilike(f"%{table.table_name}%"))
        .order_by(MetricDefinition.metric_code.asc())
        .limit(20)
        .all()
    )

    return {
        "table": _build_table_item(table, column_count, sensitive_column_count),
        "columns": [
            {
                "id": column.id,
                "column_name": column.column_name,
                "ordinal_position": column.ordinal_position,
                "data_type": column.data_type,
                "column_comment": column.column_comment,
                "business_desc": column.business_desc,
                "example_value": column.example_value,
                "is_primary_key": column.is_primary_key,
                "is_nullable": column.is_nullable,
                "is_sensitive": column.is_sensitive,
                "is_valid": column.is_valid,
            }
            for column in columns
        ],
        "related_metrics": [
            {
                "id": metric.id,
                "metric_code": metric.metric_code,
                "metric_name": metric.metric_name,
                "formula": metric.formula,
                "business_desc": metric.business_desc,
                "source_tables": metric.source_tables,
                "source_columns": metric.source_columns,
                "frequency": metric.frequency,
                "is_valid": metric.is_valid,
            }
            for metric in metrics
        ],
    }


def get_metadata_graph(db: Session) -> dict:
    column_stats = _column_stats_subquery(db)
    rows = (
        db.query(
            MetadataTable.table_name,
            MetadataTable.table_comment,
            _domain_expr().label("business_domain"),
            MetadataTable.is_valid,
            func.coalesce(column_stats.c.column_count, 0).label("column_count"),
        )
        .outerjoin(column_stats, MetadataTable.table_name == column_stats.c.table_name)
        .order_by(_domain_expr().asc(), MetadataTable.table_name.asc())
        .all()
    )

    domains: dict[str, list[dict]] = {}
    for row in rows:
        domains.setdefault(row.business_domain, []).append(
            {
                "name": row.table_comment or row.table_name.split(".")[-1],
                "value": row.column_count,
                "table_name": row.table_name,
                "table_comment": row.table_comment,
                "is_valid": row.is_valid,
            }
        )

    tree = {
        "name": "好股库元数据",
        "value": sum(row.column_count for row in rows),
        "children": [
            {
                "name": domain,
                "value": sum(item.get("value") or 0 for item in tables),
                "table_count": len(tables),
                "children": sorted(tables, key=lambda item: (-(item.get("value") or 0), item["name"])),
            }
            for domain, tables in sorted(domains.items(), key=lambda item: len(item[1]), reverse=True)
        ],
    }
    return {"tree": tree}


def get_metadata_quality(db: Session) -> dict:
    tables = db.query(MetadataTable).order_by(MetadataTable.table_name.asc()).all()
    columns = db.query(MetadataColumn).all()
    lineage_ref_counts = _lineage_ref_counts(db)
    columns_by_table: dict[str, list[MetadataColumn]] = {}
    for column in columns:
        columns_by_table.setdefault(column.table_name, []).append(column)

    total_tables = len(tables)
    valid_tables = sum(1 for table in tables if table.is_valid)
    total_columns = len(columns)
    valid_columns = [column for column in columns if column.is_valid]
    table_items = []

    for table in tables:
        table_columns = columns_by_table.get(table.table_name, [])
        item = _build_quality_table_item(table, table_columns, lineage_ref_counts.get(_table_quality_key(table.table_name), 0))
        table_items.append(item)

    unclassified_tables = sum(1 for item in table_items if _is_unclassified_domain(item["business_domain"]))
    unclassified_items = [item for item in table_items if _is_unclassified_domain(item["business_domain"])]
    tables_missing_comment = sum(1 for item in table_items if not _has_text(item["table_comment"]))
    tables_without_columns = sum(1 for item in table_items if item["column_count"] == 0)
    valid_tables_with_columns = [item for item in table_items if item["is_valid"] and item["column_count"] > 0]
    tables_without_primary_key = sum(1 for item in valid_tables_with_columns if item["primary_key_count"] == 0)
    columns_missing_comment = sum(1 for column in valid_columns if not _has_text(column.column_comment))
    columns_missing_business_desc = sum(1 for column in valid_columns if not _has_text(column.business_desc))
    columns_unknown_nullable = sum(1 for column in valid_columns if column.is_nullable is None)
    columns_missing_ordinal_position = sum(1 for column in valid_columns if column.ordinal_position is None)
    columns_type_anomaly = sum(1 for column in valid_columns if _is_type_anomaly(column.data_type))

    table_comment_coverage = _ratio(total_tables - tables_missing_comment, total_tables)
    column_comment_coverage = _ratio(len(valid_columns) - columns_missing_comment, len(valid_columns))
    primary_key_coverage = _ratio(len(valid_tables_with_columns) - tables_without_primary_key, len(valid_tables_with_columns))
    domain_quality = _build_domain_quality(table_items)

    return {
        "total_tables": total_tables,
        "valid_tables": valid_tables,
        "offline_tables": total_tables - valid_tables,
        "unclassified_tables": unclassified_tables,
        "tables_missing_comment": tables_missing_comment,
        "tables_without_columns": tables_without_columns,
        "tables_without_primary_key": tables_without_primary_key,
        "total_columns": total_columns,
        "columns_missing_comment": columns_missing_comment,
        "columns_missing_business_desc": columns_missing_business_desc,
        "columns_unknown_nullable": columns_unknown_nullable,
        "columns_missing_ordinal_position": columns_missing_ordinal_position,
        "columns_type_anomaly": columns_type_anomaly,
        "table_comment_coverage": table_comment_coverage,
        "column_comment_coverage": column_comment_coverage,
        "primary_key_coverage": primary_key_coverage,
        "issue_stats": [
            {"issue_code": "UNCLASSIFIED_TABLE", "issue_name": "待治理分类表", "count": unclassified_tables},
            {"issue_code": "TABLE_MISSING_COMMENT", "issue_name": "缺少表中文名", "count": tables_missing_comment},
            {"issue_code": "TABLE_WITHOUT_PRIMARY_KEY", "issue_name": "可用表缺少主键", "count": tables_without_primary_key},
            {"issue_code": "COLUMN_MISSING_COMMENT", "issue_name": "字段缺少中文名", "count": columns_missing_comment},
            {"issue_code": "COLUMN_MISSING_DESC", "issue_name": "字段缺少备注", "count": columns_missing_business_desc},
            {"issue_code": "COLUMN_UNKNOWN_NULLABLE", "issue_name": "字段是否为空未知", "count": columns_unknown_nullable},
            {"issue_code": "COLUMN_TYPE_ANOMALY", "issue_name": "字段类型异常", "count": columns_type_anomaly},
        ],
        "unclassified_diagnostics": _build_unclassified_diagnostics(unclassified_items),
        "domain_quality": domain_quality,
        "top_issue_tables": sorted(
            table_items,
            key=lambda item: (item["quality_score"], -len(item["issue_tags"]), -item["lineage_ref_count"], item["table_name"]),
        )[:100],
    }


def _build_table_item(table: MetadataTable, column_count: int, sensitive_column_count: int) -> dict:
    return {
        "id": table.id,
        "table_name": table.table_name,
        "table_comment": table.table_comment,
        "business_domain": table.business_domain,
        "owner": table.owner,
        "update_frequency": table.update_frequency,
        "is_valid": table.is_valid,
        "column_count": column_count,
        "sensitive_column_count": sensitive_column_count,
        "updated_at": table.updated_at,
    }


def _build_quality_table_item(table: MetadataTable, columns: list[MetadataColumn], lineage_ref_count: int) -> dict:
    column_count = len(columns)
    primary_key_count = sum(1 for column in columns if column.is_primary_key)
    missing_column_comment_count = sum(1 for column in columns if column.is_valid and not _has_text(column.column_comment))
    missing_business_desc_count = sum(1 for column in columns if column.is_valid and not _has_text(column.business_desc))
    unknown_nullable_count = sum(1 for column in columns if column.is_valid and column.is_nullable is None)
    type_anomaly_count = sum(1 for column in columns if column.is_valid and _is_type_anomaly(column.data_type))
    lifecycle_hint, lifecycle_reasons = _diagnose_table_lifecycle(
        table,
        column_count=column_count,
        primary_key_count=primary_key_count,
        missing_column_comment_count=missing_column_comment_count,
        lineage_ref_count=lineage_ref_count,
    )
    issue_tags = []

    if not table.is_valid:
        issue_tags.append("下线表")
    if _is_unclassified_domain(table.business_domain):
        issue_tags.append("待治理分类")
    if not _has_text(table.table_comment):
        issue_tags.append("缺表中文名")
    if column_count == 0:
        issue_tags.append("无字段")
    if table.is_valid and column_count > 0 and primary_key_count == 0:
        issue_tags.append("缺主键")
    if missing_column_comment_count:
        issue_tags.append("字段中文名缺失")
    if missing_business_desc_count:
        issue_tags.append("字段备注缺失")
    if unknown_nullable_count:
        issue_tags.append("是否为空未知")
    if type_anomaly_count:
        issue_tags.append("字段类型异常")
    if lifecycle_hint == "SUSPECTED_TEST_OR_TEMP":
        issue_tags.append("疑似测试临时")
    if lifecycle_hint == "SUSPECTED_STALE":
        issue_tags.append("疑似长期未更新")
    if lifecycle_hint == "SUSPECTED_UNUSED":
        issue_tags.append("疑似遗留无用")
    if lifecycle_hint == "ACTIVE_UNCLASSIFIED":
        issue_tags.append("仍被引用")

    quality_score = 100
    if not table.is_valid:
        quality_score -= 30
    if _is_unclassified_domain(table.business_domain):
        quality_score -= 18
    if not _has_text(table.table_comment):
        quality_score -= 12
    if column_count == 0:
        quality_score -= 25
    if table.is_valid and column_count > 0 and primary_key_count == 0:
        quality_score -= 15
    quality_score -= min(20, missing_column_comment_count * 2)
    quality_score -= min(12, missing_business_desc_count)
    quality_score -= min(10, unknown_nullable_count)
    quality_score -= min(10, type_anomaly_count * 2)

    return {
        "id": table.id,
        "table_name": table.table_name,
        "table_comment": table.table_comment,
        "business_domain": table.business_domain,
        "update_frequency": table.update_frequency,
        "is_valid": table.is_valid,
        "column_count": column_count,
        "primary_key_count": primary_key_count,
        "missing_column_comment_count": missing_column_comment_count,
        "missing_business_desc_count": missing_business_desc_count,
        "unknown_nullable_count": unknown_nullable_count,
        "lineage_ref_count": lineage_ref_count,
        "quality_score": max(0, quality_score),
        "issue_tags": issue_tags,
        "lifecycle_hint": lifecycle_hint,
        "lifecycle_reasons": lifecycle_reasons,
        "source_collected_at": table.source_collected_at,
        "latest_creat_tm": table.latest_creat_tm,
        "updated_at": table.updated_at,
    }


def _build_unclassified_diagnostics(items: list[dict]) -> list[dict]:
    definitions = {
        "ACTIVE_UNCLASSIFIED": {
            "diagnostic_name": "仍被血缘引用",
            "description": "未分类但仍出现在存储过程读写血缘中，优先补业务分类。",
        },
        "SUSPECTED_TEST_OR_TEMP": {
            "diagnostic_name": "疑似测试或临时表",
            "description": "表名包含 test、tmp、temp、bak、delete、old 等信号，需确认是否应下线或排除。",
        },
        "SUSPECTED_STALE": {
            "diagnostic_name": "疑似长期未更新",
            "description": "未分类、无血缘引用，且源端 latest_creat_tm 距今超过两年，可优先排除或降级。",
        },
        "SUSPECTED_UNUSED": {
            "diagnostic_name": "疑似遗留无用表",
            "description": "无血缘引用、缺少表中文名且缺主键，可能是历史遗留或低价值表。",
        },
        "NEEDS_CLASSIFICATION": {
            "diagnostic_name": "待补业务分类",
            "description": "未分类且未命中明显测试/遗留信号，需要人工补充业务域。",
        },
        "OFFLINE": {
            "diagnostic_name": "已下线",
            "description": "源端已标记为下线，不应进入后续 AI 问答候选。",
        },
    }
    counts: dict[str, int] = {}
    for item in items:
        hint = item.get("lifecycle_hint") or "NEEDS_CLASSIFICATION"
        counts[hint] = counts.get(hint, 0) + 1
    return [
        {
            "diagnostic_code": code,
            "diagnostic_name": meta["diagnostic_name"],
            "count": counts.get(code, 0),
            "description": meta["description"],
        }
        for code, meta in definitions.items()
    ]


def _diagnose_table_lifecycle(
    table: MetadataTable,
    *,
    column_count: int,
    primary_key_count: int,
    missing_column_comment_count: int,
    lineage_ref_count: int,
) -> tuple[str, list[str]]:
    if not table.is_valid:
        return "OFFLINE", ["源端已标记为下线表。"]

    reasons = []
    table_name = table.table_name or ""
    is_unclassified = _is_unclassified_domain(table.business_domain)
    if is_unclassified and lineage_ref_count > 0:
        reasons.append(f"当前血缘中仍有 {lineage_ref_count} 次读写引用。")
        if not _has_text(table.table_comment):
            reasons.append("缺少表中文名，影响后续 RAG 和人工理解。")
        return "ACTIVE_UNCLASSIFIED", reasons

    if is_unclassified and _looks_like_test_or_temp_table(table_name):
        reasons.append("表名命中测试、临时、备份、删除或历史遗留命名信号。")
        if lineage_ref_count == 0:
            reasons.append("当前血缘中没有读写引用。")
        if table.latest_creat_tm:
            reasons.append(f"源端最近创建时间信号为 {table.latest_creat_tm.date()}。")
        return "SUSPECTED_TEST_OR_TEMP", reasons

    if is_unclassified and lineage_ref_count == 0 and _is_source_time_stale(table.latest_creat_tm):
        reasons.append("当前血缘中没有读写引用。")
        reasons.append(f"源端最近创建时间信号为 {table.latest_creat_tm.date()}，距今超过 {STALE_SOURCE_DAYS} 天。")
        if not _has_text(table.table_comment):
            reasons.append("缺少表中文名。")
        return "SUSPECTED_STALE", reasons

    if is_unclassified and lineage_ref_count == 0 and not _has_text(table.table_comment) and primary_key_count == 0:
        reasons.append("当前血缘中没有读写引用。")
        reasons.append("缺少表中文名。")
        if column_count > 0:
            reasons.append("没有主键信息。")
        if missing_column_comment_count:
            reasons.append("字段中文名缺失较多。")
        return "SUSPECTED_UNUSED", reasons

    if is_unclassified:
        reasons.append("业务域仍为未分类，需要人工补充或进入推荐分类流程。")
        if not _has_text(table.table_comment):
            reasons.append("缺少表中文名。")
        return "NEEDS_CLASSIFICATION", reasons

    return "NORMAL", ["已有业务域分类。"]


def _build_domain_quality(table_items: list[dict]) -> list[dict]:
    domains: dict[str, list[dict]] = {}
    for item in table_items:
        domain = item["business_domain"] or UNKNOWN_DOMAIN
        domains.setdefault(domain, []).append(item)
    rows = []
    for domain, items in domains.items():
        rows.append(
            {
                "business_domain": domain,
                "table_count": len(items),
                "valid_table_count": sum(1 for item in items if item["is_valid"]),
                "avg_quality_score": round(sum(item["quality_score"] for item in items) / len(items), 2),
                "unclassified": _is_unclassified_domain(domain),
            }
        )
    return sorted(rows, key=lambda row: (not row["unclassified"], -row["table_count"], row["business_domain"]))


def _lineage_ref_counts(db: Session) -> dict[str, int]:
    rows = (
        db.query(ProcedureLineageEdge.source_object, ProcedureLineageEdge.target_object, ProcedureLineageEdge.relation_type)
        .filter(ProcedureLineageEdge.relation_type.in_(["READ", "WRITE"]))
        .all()
    )
    counts: dict[str, int] = {}
    for source_object, target_object, relation_type in rows:
        object_name = source_object if relation_type == "READ" else target_object
        if not object_name:
            continue
        key = _table_quality_key(object_name)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _table_quality_key(table_name: str) -> str:
    return table_name.split(".")[-1].strip().lower()


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _is_unclassified_domain(domain: str | None) -> bool:
    return (domain or "").strip() in UNCLASSIFIED_DOMAINS


def _is_type_anomaly(data_type: str | None) -> bool:
    if not _has_text(data_type):
        return True
    normalized = data_type.strip().lower()
    return "(-1)" in normalized


def _looks_like_test_or_temp_table(table_name: str) -> bool:
    short_name = _table_quality_key(table_name)
    return any(token in short_name for token in TEST_OR_TEMP_TABLE_TOKENS)


def _is_source_time_stale(value: datetime | None) -> bool:
    if value is None:
        return False
    current = datetime.now(timezone.utc)
    normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized < current - timedelta(days=STALE_SOURCE_DAYS)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0
    return round(numerator * 100 / denominator, 2)
