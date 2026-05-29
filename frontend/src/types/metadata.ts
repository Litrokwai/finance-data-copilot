export interface MetadataDomainStat {
  business_domain: string;
  table_count: number;
}

export interface MetadataTopTable {
  table_name: string;
  business_domain: string;
  column_count: number;
}

export interface MetadataSummary {
  total_tables: number;
  valid_tables: number;
  offline_tables: number;
  total_columns: number;
  valid_columns: number;
  sensitive_columns: number;
  total_metrics: number;
  valid_metrics: number;
  domain_distribution: MetadataDomainStat[];
  top_table_columns: MetadataTopTable[];
}

export interface MetadataTableListItem {
  id: number;
  table_name: string;
  table_comment?: string;
  business_domain?: string;
  owner?: string;
  update_frequency?: string;
  is_valid: boolean;
  column_count: number;
  sensitive_column_count: number;
  updated_at?: string;
}

export interface MetadataTableList {
  items: MetadataTableListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MetadataColumnItem {
  id: number;
  column_name: string;
  ordinal_position?: number;
  data_type?: string;
  column_comment?: string;
  business_desc?: string;
  example_value?: string;
  is_primary_key: boolean;
  is_nullable?: boolean | null;
  is_sensitive: boolean;
  is_valid: boolean;
}

export interface MetadataMetricItem {
  id: number;
  metric_code: string;
  metric_name: string;
  formula?: string;
  business_desc?: string;
  source_tables?: string[];
  source_columns?: string[];
  frequency?: string;
  is_valid: boolean;
}

export interface MetadataTableDetail {
  table: MetadataTableListItem;
  columns: MetadataColumnItem[];
  related_metrics: MetadataMetricItem[];
}

export interface MetadataGraphNode {
  name: string;
  value?: number;
  table_name?: string;
  table_comment?: string;
  table_count?: number;
  is_valid?: boolean;
  children?: MetadataGraphNode[];
}

export interface MetadataGraph {
  tree: MetadataGraphNode;
}

export interface MetadataTableQuery {
  keyword?: string;
  business_domain?: string;
  is_valid?: boolean;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}
