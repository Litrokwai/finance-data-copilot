import request from "./request";
import type { ApiResponse } from "../types/sql";
import type {
  LineageGraph,
  LineageReviewItem,
  LineageReviewQuery,
  LineageReviewSummary,
  LineageReviewUpdate,
  LineageSummary,
  LineageTableImpact,
  LineageTableUsage,
  ProcedureLineageDetail,
  ProcedureLineageItem,
  ProcedureLineageQuery
} from "../types/lineage";

export function getLineageSummary() {
  return request.get<ApiResponse<LineageSummary>>("/api/lineage/summary").then((res) => res.data.data);
}

export function getProcedureLineageList(params?: ProcedureLineageQuery) {
  return request.get<ApiResponse<ProcedureLineageItem[]>>("/api/lineage/procedures", { params }).then((res) => res.data.data);
}

export function getProcedureLineageDetail(id: number) {
  return request.get<ApiResponse<ProcedureLineageDetail>>(`/api/lineage/procedures/${id}`).then((res) => res.data.data);
}

export function getLineageGraph(params?: ProcedureLineageQuery) {
  return request.get<ApiResponse<LineageGraph>>("/api/lineage/graph", { params }).then((res) => res.data.data);
}

export function getLineageTables(params?: Pick<ProcedureLineageQuery, "keyword" | "limit">) {
  return request.get<ApiResponse<LineageTableUsage[]>>("/api/lineage/tables", { params }).then((res) => res.data.data);
}

export function getLineageTableImpact(tableName: string) {
  return request
    .get<ApiResponse<LineageTableImpact>>("/api/lineage/table-impact", { params: { table_name: tableName } })
    .then((res) => res.data.data);
}

export function getLineageReviewSummary(params?: Pick<LineageReviewQuery, "confidence_threshold">) {
  return request.get<ApiResponse<LineageReviewSummary>>("/api/lineage/review/summary", { params }).then((res) => res.data.data);
}

export function getLineageReviewItems(params?: LineageReviewQuery) {
  return request.get<ApiResponse<LineageReviewItem[]>>("/api/lineage/review/items", { params }).then((res) => res.data.data);
}

export function updateLineageReviewItem(payload: LineageReviewUpdate) {
  return request.post<ApiResponse<LineageReviewUpdate>>("/api/lineage/review/items", payload).then((res) => res.data.data);
}
