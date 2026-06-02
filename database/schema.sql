DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN
        CREATE EXTENSION IF NOT EXISTS vector;
    ELSE
        RAISE NOTICE 'pgvector extension is not installed locally; skip vector extension for V1.';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS sql_analysis_record (
    id SERIAL PRIMARY KEY,
    raw_sql TEXT NOT NULL,
    sql_type VARCHAR(50),
    summary TEXT,
    involved_tables JSONB,
    involved_columns JSONB,
    join_relations JSONB,
    where_conditions JSONB,
    risk_level VARCHAR(20),
    risk_items JSONB,
    analysis_result_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sql_analysis_record_created_at ON sql_analysis_record(created_at);
CREATE INDEX IF NOT EXISTS idx_sql_analysis_record_risk_level ON sql_analysis_record(risk_level);

CREATE TABLE IF NOT EXISTS metadata_table (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL UNIQUE,
    table_comment TEXT,
    business_domain VARCHAR(100),
    owner VARCHAR(100),
    update_frequency VARCHAR(50),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metadata_table_domain ON metadata_table(business_domain);

CREATE TABLE IF NOT EXISTS metadata_column (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    ordinal_position INTEGER,
    data_type VARCHAR(100),
    column_comment TEXT,
    business_desc TEXT,
    example_value TEXT,
    is_primary_key BOOLEAN NOT NULL DEFAULT FALSE,
    is_nullable BOOLEAN,
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metadata_column_table_column ON metadata_column(table_name, column_name);
CREATE INDEX IF NOT EXISTS idx_metadata_column_table_order ON metadata_column(table_name, is_primary_key, ordinal_position);

CREATE TABLE IF NOT EXISTS metric_definition (
    id SERIAL PRIMARY KEY,
    metric_code VARCHAR(100) NOT NULL UNIQUE,
    metric_name VARCHAR(255) NOT NULL,
    formula TEXT,
    business_desc TEXT,
    source_tables JSONB,
    source_columns JSONB,
    dimension TEXT,
    frequency VARCHAR(50),
    example_sql TEXT,
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metric_definition_metric_code ON metric_definition(metric_code);

CREATE TABLE IF NOT EXISTS procedure_lineage_record (
    id SERIAL PRIMARY KEY,
    procedure_name VARCHAR(255) NOT NULL UNIQUE,
    procedure_schema VARCHAR(128),
    database_name VARCHAR(128),
    source_system VARCHAR(100),
    definition_hash VARCHAR(64),
    read_tables JSONB DEFAULT '[]'::jsonb,
    write_tables JSONB DEFAULT '[]'::jsonb,
    temp_tables JSONB DEFAULT '[]'::jsonb,
    lineage_edges JSONB DEFAULT '[]'::jsonb,
    statement_count INTEGER NOT NULL DEFAULT 0,
    parse_status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
    parse_message TEXT,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_procedure_lineage_record_procedure_name ON procedure_lineage_record(procedure_name);
CREATE INDEX IF NOT EXISTS idx_procedure_lineage_record_synced_at ON procedure_lineage_record(synced_at);

CREATE TABLE IF NOT EXISTS procedure_lineage_edge (
    id SERIAL PRIMARY KEY,
    procedure_id INTEGER NOT NULL REFERENCES procedure_lineage_record(id) ON DELETE CASCADE,
    procedure_name VARCHAR(255) NOT NULL,
    source_object VARCHAR(512) NOT NULL,
    target_object VARCHAR(512) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    source_kind VARCHAR(50) NOT NULL DEFAULT 'table',
    target_kind VARCHAR(50) NOT NULL DEFAULT 'table',
    statement_index INTEGER,
    statement_type VARCHAR(50),
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.8,
    statement_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_procedure_lineage_edge_procedure_id ON procedure_lineage_edge(procedure_id);
CREATE INDEX IF NOT EXISTS idx_procedure_lineage_edge_procedure_name ON procedure_lineage_edge(procedure_name);
CREATE INDEX IF NOT EXISTS idx_procedure_lineage_edge_source_object ON procedure_lineage_edge(source_object);
CREATE INDEX IF NOT EXISTS idx_procedure_lineage_edge_target_object ON procedure_lineage_edge(target_object);
CREATE INDEX IF NOT EXISTS idx_procedure_lineage_edge_relation_type ON procedure_lineage_edge(relation_type);

CREATE TABLE IF NOT EXISTS lineage_review_record (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,
    review_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    review_note TEXT,
    reviewer VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_lineage_review_target UNIQUE (target_type, target_id)
);

CREATE INDEX IF NOT EXISTS idx_lineage_review_record_target_type ON lineage_review_record(target_type);
CREATE INDEX IF NOT EXISTS idx_lineage_review_record_target_id ON lineage_review_record(target_id);
CREATE INDEX IF NOT EXISTS idx_lineage_review_record_review_status ON lineage_review_record(review_status);
