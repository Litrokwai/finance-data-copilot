export type RiskLevel = "HIGH" | "MEDIUM" | "LOW";

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface SqlRiskResult {
  risk_level: RiskLevel;
  risk_items: string[];
  suggestions: string[];
}

export interface SqlAnalyzeResult extends SqlRiskResult {
  sql_type: string;
  summary: string;
  involved_tables: string[];
  involved_columns: string[];
  join_relations: Array<Record<string, string>>;
  where_conditions: string[];
  analysis_result_json: Record<string, unknown>;
}

export interface SqlHistoryItem {
  id: number;
  raw_sql: string;
  sql_type?: string;
  summary?: string;
  involved_tables?: string[];
  involved_columns?: string[];
  join_relations?: Array<Record<string, string>>;
  where_conditions?: string[];
  risk_level?: RiskLevel;
  risk_items?: string[];
  analysis_result_json?: Record<string, unknown>;
  created_at: string;
}

export interface DashboardSummary {
  total_analysis_count: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  recent_analysis_count: number;
  trend: Array<{ date: string; count: number }>;
}
