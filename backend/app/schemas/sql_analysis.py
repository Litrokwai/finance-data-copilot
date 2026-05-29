from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any


class SqlAnalyzeRequest(BaseModel):
    raw_sql: str = Field(..., min_length=1)


class SqlRiskCheckRequest(BaseModel):
    raw_sql: str = Field(..., min_length=1)


class SqlRiskResult(BaseModel):
    risk_level: str
    risk_items: list[str]
    suggestions: list[str]


class SqlAnalyzeResult(SqlRiskResult):
    sql_type: str
    summary: str
    involved_tables: list[str]
    involved_columns: list[str]
    join_relations: list[dict[str, Any]]
    where_conditions: list[str]
    analysis_result_json: dict[str, Any]


class SqlHistoryItem(BaseModel):
    id: int
    raw_sql: str
    sql_type: str | None = None
    summary: str | None = None
    involved_tables: list[str] | None = None
    involved_columns: list[str] | None = None
    join_relations: list[dict[str, Any]] | None = None
    where_conditions: list[str] | None = None
    risk_level: str | None = None
    risk_items: list[str] | None = None
    analysis_result_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
