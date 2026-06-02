from datetime import datetime

from pydantic import BaseModel


class MetadataDomainStat(BaseModel):
    business_domain: str
    table_count: int


class MetadataTopTable(BaseModel):
    table_name: str
    business_domain: str
    column_count: int


class MetadataSummary(BaseModel):
    total_tables: int
    valid_tables: int
    offline_tables: int
    total_columns: int
    valid_columns: int
    sensitive_columns: int
    total_metrics: int
    valid_metrics: int
    domain_distribution: list[MetadataDomainStat]
    top_table_columns: list[MetadataTopTable]


class MetadataTableListItem(BaseModel):
    id: int
    table_name: str
    table_comment: str | None = None
    business_domain: str | None = None
    owner: str | None = None
    update_frequency: str | None = None
    is_valid: bool
    column_count: int
    sensitive_column_count: int
    updated_at: datetime | None = None


class MetadataTableList(BaseModel):
    items: list[MetadataTableListItem]
    total: int
    page: int
    page_size: int


class MetadataColumnItem(BaseModel):
    id: int
    column_name: str
    ordinal_position: int | None = None
    data_type: str | None = None
    column_comment: str | None = None
    business_desc: str | None = None
    example_value: str | None = None
    is_primary_key: bool = False
    is_nullable: bool | None = None
    is_sensitive: bool
    is_valid: bool


class MetadataMetricItem(BaseModel):
    id: int
    metric_code: str
    metric_name: str
    formula: str | None = None
    business_desc: str | None = None
    source_tables: list[str] | None = None
    source_columns: list[str] | None = None
    frequency: str | None = None
    is_valid: bool


class MetadataTableDetail(BaseModel):
    table: MetadataTableListItem
    columns: list[MetadataColumnItem]
    related_metrics: list[MetadataMetricItem]


class MetadataGraph(BaseModel):
    tree: dict


class MetadataQualityIssueStat(BaseModel):
    issue_code: str
    issue_name: str
    count: int


class MetadataQualityDomainStat(BaseModel):
    business_domain: str
    table_count: int
    valid_table_count: int
    avg_quality_score: float
    unclassified: bool


class MetadataQualityTableItem(BaseModel):
    id: int
    table_name: str
    table_comment: str | None = None
    business_domain: str | None = None
    update_frequency: str | None = None
    is_valid: bool
    column_count: int
    primary_key_count: int
    missing_column_comment_count: int
    missing_business_desc_count: int
    unknown_nullable_count: int
    lineage_ref_count: int
    quality_score: int
    issue_tags: list[str]
    lifecycle_hint: str
    lifecycle_reasons: list[str]
    updated_at: datetime | None = None


class MetadataUnclassifiedDiagnosticStat(BaseModel):
    diagnostic_code: str
    diagnostic_name: str
    count: int
    description: str


class MetadataQualitySummary(BaseModel):
    total_tables: int
    valid_tables: int
    offline_tables: int
    unclassified_tables: int
    tables_missing_comment: int
    tables_without_columns: int
    tables_without_primary_key: int
    total_columns: int
    columns_missing_comment: int
    columns_missing_business_desc: int
    columns_unknown_nullable: int
    columns_missing_ordinal_position: int
    columns_type_anomaly: int
    table_comment_coverage: float
    column_comment_coverage: float
    primary_key_coverage: float
    issue_stats: list[MetadataQualityIssueStat]
    unclassified_diagnostics: list[MetadataUnclassifiedDiagnosticStat]
    domain_quality: list[MetadataQualityDomainStat]
    top_issue_tables: list[MetadataQualityTableItem]
