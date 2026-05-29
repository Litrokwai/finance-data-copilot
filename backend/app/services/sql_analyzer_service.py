from typing import Any

import sqlglot
from sqlglot import exp

from app.ai.llm_client import explain_sql_with_llm
from app.models.sql_analysis_record import SqlAnalysisRecord
from app.services.sql_risk_service import check_sql_risk


def _extract_sql_type(expression: exp.Expression) -> str:
    if isinstance(expression, exp.Select):
        return "SELECT"
    if isinstance(expression, exp.Insert):
        return "INSERT"
    if isinstance(expression, exp.Update):
        return "UPDATE"
    if isinstance(expression, exp.Delete):
        return "DELETE"
    if isinstance(expression, exp.Create):
        return "CREATE"
    if isinstance(expression, exp.Drop):
        return "DROP"
    return expression.key.upper() if expression.key else "UNKNOWN"


def _extract_tables(expression: exp.Expression) -> list[str]:
    tables = []
    for table in expression.find_all(exp.Table):
        table_name = table.sql(dialect="postgres")
        if table_name not in tables:
            tables.append(table_name)
    return tables


def _extract_columns(expression: exp.Expression) -> list[str]:
    columns = []
    for column in expression.find_all(exp.Column):
        column_name = column.sql(dialect="postgres")
        if column_name not in columns:
            columns.append(column_name)
    return columns


def _extract_join_relations(expression: exp.Expression) -> list[dict[str, Any]]:
    joins = []
    for join in expression.find_all(exp.Join):
        joins.append(
            {
                "join_type": (join.args.get("kind") or "JOIN").upper(),
                "table": join.this.sql(dialect="postgres") if join.this else "",
                "on": join.args["on"].sql(dialect="postgres") if join.args.get("on") else "",
            }
        )
    return joins


def _extract_where_conditions(expression: exp.Expression) -> list[str]:
    where = expression.find(exp.Where)
    if not where:
        return []
    return [where.this.sql(dialect="postgres")] if where.this else []


def analyze_sql(raw_sql: str) -> dict[str, Any]:
    try:
        expression = sqlglot.parse_one(raw_sql, read="postgres")
    except Exception as exc:
        risk = check_sql_risk(raw_sql)
        return {
            "sql_type": "UNKNOWN",
            "summary": "SQL 解析失败，请检查语法是否完整。",
            "involved_tables": [],
            "involved_columns": [],
            "join_relations": [],
            "where_conditions": [],
            "risk_level": risk["risk_level"],
            "risk_items": [*risk["risk_items"], f"SQLGlot 解析失败：{exc}"],
            "suggestions": ["检查 SQL 关键字、括号、别名和字符串引号是否正确。", *risk["suggestions"]],
            "analysis_result_json": {"parse_error": str(exc), "raw_sql": raw_sql},
        }

    parsed_info = {
        "sql_type": _extract_sql_type(expression),
        "involved_tables": _extract_tables(expression),
        "involved_columns": _extract_columns(expression),
        "join_relations": _extract_join_relations(expression),
        "where_conditions": _extract_where_conditions(expression),
    }
    risk = check_sql_risk(raw_sql)
    llm_result = explain_sql_with_llm(raw_sql, parsed_info)

    analysis_result_json = {
        "parsed": parsed_info,
        "risk": risk,
        "llm": llm_result,
        "normalized_sql": expression.sql(dialect="postgres"),
    }

    return {
        **parsed_info,
        "summary": llm_result["summary"],
        "risk_level": risk["risk_level"],
        "risk_items": risk["risk_items"],
        "suggestions": llm_result.get("suggestions", []) + risk["suggestions"],
        "analysis_result_json": analysis_result_json,
    }


def build_analysis_record(raw_sql: str, result: dict[str, Any]) -> SqlAnalysisRecord:
    return SqlAnalysisRecord(
        raw_sql=raw_sql,
        sql_type=result["sql_type"],
        summary=result["summary"],
        involved_tables=result["involved_tables"],
        involved_columns=result["involved_columns"],
        join_relations=result["join_relations"],
        where_conditions=result["where_conditions"],
        risk_level=result["risk_level"],
        risk_items=result["risk_items"],
        analysis_result_json=result["analysis_result_json"],
    )
