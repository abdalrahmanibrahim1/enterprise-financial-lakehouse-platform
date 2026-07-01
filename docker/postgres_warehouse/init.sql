CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS metadata.pipeline_runs (
    batch_id TEXT PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    rows_extracted INTEGER DEFAULT 0,
    rows_landed INTEGER DEFAULT 0,
    rows_bronze_loaded INTEGER DEFAULT 0,
    rows_silver_loaded INTEGER DEFAULT 0,
    rows_gold_loaded INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metadata.pipeline_watermarks (
    source_system TEXT NOT NULL,
    source_table TEXT NOT NULL,
    watermark_column TEXT NOT NULL,
    last_watermark_value TEXT,
    -- Stored as TEXT to support timestamp, date, file-name, and hash-based watermarks.
    last_successful_batch TEXT,
    -- Logical reference to metadata.pipeline_runs(batch_id); not enforced yet to keep metadata recovery flexible.
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (source_system, source_table)
);

CREATE TABLE IF NOT EXISTS metadata.data_quality_results (
    quality_result_id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    layer TEXT NOT NULL,
    object_name TEXT NOT NULL,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL,
    failed_row_count INTEGER DEFAULT 0,
    checked_row_count INTEGER DEFAULT 0,
    details TEXT,
    checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metadata.rejected_records (
    rejection_id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    source_system TEXT NOT NULL,
    layer TEXT NOT NULL,
    object_name TEXT NOT NULL,
    record_identifier TEXT,
    rejection_reason TEXT NOT NULL,
    raw_payload JSONB,
    rejected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metadata.lake_file_registry (
    file_id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    zone TEXT NOT NULL,
    object_path TEXT NOT NULL,
    object_format TEXT NOT NULL,
    source_system TEXT,
    dataset_name TEXT NOT NULL,
    row_count INTEGER,
    file_size_bytes BIGINT,
    record_hash TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON metadata.pipeline_runs(status);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at
    ON metadata.pipeline_runs(started_at);

CREATE INDEX IF NOT EXISTS idx_data_quality_results_batch_id
    ON metadata.data_quality_results(batch_id);

CREATE INDEX IF NOT EXISTS idx_data_quality_results_status
    ON metadata.data_quality_results(status);

CREATE INDEX IF NOT EXISTS idx_rejected_records_batch_id
    ON metadata.rejected_records(batch_id);

CREATE INDEX IF NOT EXISTS idx_rejected_records_object_name
    ON metadata.rejected_records(object_name);

CREATE INDEX IF NOT EXISTS idx_lake_file_registry_batch_id
    ON metadata.lake_file_registry(batch_id);

CREATE INDEX IF NOT EXISTS idx_lake_file_registry_zone
    ON metadata.lake_file_registry(zone);

CREATE INDEX IF NOT EXISTS idx_lake_file_registry_dataset_name
    ON metadata.lake_file_registry(dataset_name);