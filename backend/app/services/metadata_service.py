from __future__ import annotations

from sqlalchemy import String, case, cast, func, or_
from sqlalchemy.orm import Session

from app.models.metadata_column import MetadataColumn
from app.models.metadata_table import MetadataTable
from app.models.metric_definition import MetricDefinition


UNKNOWN_DOMAIN = "未分类"


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
