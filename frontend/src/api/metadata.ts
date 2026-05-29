import request from "./request";
import type { ApiResponse } from "../types/sql";
import type {
  MetadataGraph,
  MetadataSummary,
  MetadataTableDetail,
  MetadataTableList,
  MetadataTableQuery
} from "../types/metadata";

export function getMetadataSummary() {
  return request.get<ApiResponse<MetadataSummary>>("/api/metadata/summary").then((res) => res.data.data);
}

export function getMetadataTables(params: MetadataTableQuery) {
  return request.get<ApiResponse<MetadataTableList>>("/api/metadata/tables", { params }).then((res) => res.data.data);
}

export function getMetadataTableDetail(tableId: number) {
  return request.get<ApiResponse<MetadataTableDetail>>(`/api/metadata/tables/${tableId}`).then((res) => res.data.data);
}

export function getMetadataGraph() {
  return request.get<ApiResponse<MetadataGraph>>("/api/metadata/graph").then((res) => res.data.data);
}
