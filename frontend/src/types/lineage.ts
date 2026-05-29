export interface LineageSummary {
  total_procedures: number;
  total_read_tables: number;
  total_write_tables: number;
  total_edges: number;
  review_count: number;
  latest_sync_time?: string;
}

export interface ProcedureLineageQuery {
  keyword?: string;
  parse_status?: "SUCCESS" | "REVIEW";
  max_procedures?: number;
  limit?: number;
}

export interface ProcedureLineageItem {
  id: number;
  procedure_name: string;
  procedure_schema?: string;
  database_name?: string;
  source_system?: string;
  read_table_count: number;
  write_table_count: number;
  temp_table_count: number;
  edge_count: number;
  table_flow_count: number;
  statement_count: number;
  parse_status: string;
  parse_message?: string;
  synced_at?: string;
}

export interface ProcedureLineageDetail extends ProcedureLineageItem {
  read_tables: string[];
  write_tables: string[];
  temp_tables: string[];
  lineage_edges: Array<{ source: string; target: string; relation: string }>;
  structured_edges: ProcedureLineageEdge[];
}

export interface ProcedureLineageEdge {
  id: number;
  source_object: string;
  target_object: string;
  relation_type: "READ" | "WRITE" | "TABLE_FLOW";
  source_kind: "procedure" | "table" | "temp_table";
  target_kind: "procedure" | "table" | "temp_table";
  statement_index?: number;
  statement_type?: string;
  confidence: number;
  statement_snippet?: string;
}

export interface LineageTableUsage {
  table_name: string;
  read_by_count: number;
  write_by_count: number;
  read_edge_count: number;
  write_edge_count: number;
  edge_count: number;
}

export interface ProcedureRef {
  procedure_id: number;
  procedure_name: string;
}

export interface LineageTableImpact {
  table_name: string;
  read_by_procedures: ProcedureRef[];
  write_by_procedures: ProcedureRef[];
  read_edges: ProcedureLineageEdge[];
  write_edges: ProcedureLineageEdge[];
  table_flow_edges: ProcedureLineageEdge[];
}

export interface LineageGraphNode {
  id: string;
  name: string;
  full_name?: string;
  category: "procedure" | "read_table" | "write_table" | "temp_table";
  symbolSize?: number;
  value?: number;
}

export interface LineageGraphEdge {
  source: string;
  target: string;
  relation: "READ" | "WRITE";
}

export interface LineageGraph {
  nodes: LineageGraphNode[];
  edges: LineageGraphEdge[];
}
