import re


HIGH_RISK_KEYWORDS = {
    "DELETE": "包含 DELETE 操作，可能删除业务数据。",
    "UPDATE": "包含 UPDATE 操作，可能修改业务数据。",
    "DROP": "包含 DROP 操作，可能删除数据库对象。",
    "TRUNCATE": "包含 TRUNCATE 操作，可能清空整张表。",
}


def check_sql_risk(raw_sql: str) -> dict[str, list[str] | str]:
    normalized = re.sub(r"\s+", " ", raw_sql.strip())
    upper_sql = normalized.upper()
    risk_items: list[str] = []
    suggestions: list[str] = []

    if re.search(r"SELECT\s+\*", upper_sql):
        risk_items.append("存在 SELECT *，可能读取过多字段。")
        suggestions.append("明确选择需要的字段，减少网络传输和字段口径误用。")

    has_where = " WHERE " in f" {upper_sql} "
    if not has_where and any(keyword in upper_sql for keyword in ["SELECT", "UPDATE", "DELETE"]):
        risk_items.append("缺少 WHERE 条件，可能造成全表扫描或批量修改。")
        suggestions.append("补充业务日期、分区字段、主键或状态过滤条件。")

    for keyword, message in HIGH_RISK_KEYWORDS.items():
        if re.search(rf"\b{keyword}\b", upper_sql):
            risk_items.append(message)
            suggestions.append(f"{keyword} 类 SQL 上线前必须人工复核，并确认备份与回滚方案。")

    if "SELECT" in upper_sql and not has_where and " LIMIT " not in upper_sql:
        risk_items.append("可能存在大表全表扫描。")
        suggestions.append("增加 WHERE 条件或 LIMIT，避免在大表上进行无界查询。")

    date_patterns = [
        r"\bDATE\b",
        r"\bDT\b",
        r"\bTRADE_DATE\b",
        r"\bBUSINESS_DATE\b",
        r"\bCREATED_AT\b",
        r"\bUPDATED_AT\b",
    ]
    if "SELECT" in upper_sql and not any(re.search(pattern, upper_sql) for pattern in date_patterns):
        risk_items.append("缺少明显日期或时间条件。")
        suggestions.append("金融数据分析通常需要限制交易日、业务日期或更新时间范围。")

    if any(keyword in upper_sql for keyword in ["DROP", "TRUNCATE", "DELETE", "UPDATE"]):
        risk_level = "HIGH"
    elif len(risk_items) >= 2:
        risk_level = "MEDIUM"
    elif risk_items:
        risk_level = "LOW"
    else:
        risk_level = "LOW"
        suggestions.append("未发现明显风险，仍建议结合表规模和索引情况复核执行计划。")

    return {
        "risk_level": risk_level,
        "risk_items": risk_items,
        "suggestions": list(dict.fromkeys(suggestions)),
    }
