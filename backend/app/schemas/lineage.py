from pydantic import BaseModel


class ProcedureLineageSummary(BaseModel):
    total_procedures: int
    total_read_tables: int
    total_write_tables: int
    total_edges: int
    review_count: int = 0
    latest_sync_time: str | None = None


class ProcedureLineageItem(BaseModel):
    id: int
    procedure_name: str
    procedure_schema: str | None = None
    database_name: str | None = None
    source_system: str | None = None
    read_table_count: int
    write_table_count: int
    temp_table_count: int
    edge_count: int = 0
    table_flow_count: int = 0
    statement_count: int
    parse_status: str
    parse_message: str | None = None
    synced_at: str | None = None


class ProcedureLineageDetail(ProcedureLineageItem):
    read_tables: list[str]
    write_tables: list[str]
    temp_tables: list[str]
    lineage_edges: list[dict]
    structured_edges: list[dict] = []


class ProcedureLineageGraph(BaseModel):
    nodes: list[dict]
    edges: list[dict]
