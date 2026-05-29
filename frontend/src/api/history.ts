import request from "./request";
import type { ApiResponse, SqlHistoryItem } from "../types/sql";

export function getHistory() {
  return request.get<ApiResponse<SqlHistoryItem[]>>("/api/history").then((res) => res.data.data);
}
