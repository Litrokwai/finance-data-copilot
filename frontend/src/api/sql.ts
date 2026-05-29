import request from "./request";
import type { ApiResponse, SqlAnalyzeResult, SqlRiskResult } from "../types/sql";

export function analyzeSql(raw_sql: string) {
  return request.post<ApiResponse<SqlAnalyzeResult>>("/api/sql/analyze", { raw_sql }).then((res) => res.data.data);
}

export function checkSqlRisk(raw_sql: string) {
  return request.post<ApiResponse<SqlRiskResult>>("/api/sql/risk-check", { raw_sql }).then((res) => res.data.data);
}
