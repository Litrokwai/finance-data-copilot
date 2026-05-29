import request from "./request";
import type { ApiResponse, DashboardSummary } from "../types/sql";

export function getDashboardSummary() {
  return request.get<ApiResponse<DashboardSummary>>("/api/dashboard/summary").then((res) => res.data.data);
}
