from typing import Any

from app.core.config import get_settings


def explain_sql_with_llm(raw_sql: str, parsed_info: dict[str, Any]) -> dict[str, Any]:
    """Unified LLM entrypoint. V1 returns a mock result unless an API key is configured."""
    settings = get_settings()
    tables = ", ".join(parsed_info.get("involved_tables") or []) or "未识别到表"
    sql_type = parsed_info.get("sql_type", "UNKNOWN")

    if not settings.llm_api_key:
        return {
            "summary": f"这是一段 {sql_type} SQL，主要涉及 {tables}。当前版本使用本地规则解析，后续可接入真实大模型生成更完整解释。",
            "suggestions": [
                "确认过滤条件是否覆盖业务日期或分区字段。",
                "检查 JOIN 条件是否完整，避免产生重复记录或笛卡尔积。",
                "上线前结合数据字典核对字段口径。",
            ],
            "provider": "mock",
        }

    return {
        "summary": f"已检测到 LLM API Key，可在 llm_client.py 中接入真实模型。当前 SQL 类型为 {sql_type}。",
        "suggestions": ["替换 mock 逻辑后，可输出更细粒度的业务解释和优化建议。"],
        "provider": settings.llm_model,
    }
