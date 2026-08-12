from datetime import datetime

from src.connectors.postgres_connector import get_warehouse_connection

def create_pipeline_run(
    batch_id,
    pipeline_name,
    trigger_type,
    cursor,
):
    query = """
    INSERT INTO metadata.pipeline_runs (
        batch_id,
        pipeline_name,
        started_at,
        status,
        trigger_type
    )
    VALUES (
        %s,
        %s,
        CURRENT_TIMESTAMP,
        'STARTED',
        %s
    );
    """

    cursor.execute(
        query,
        (
            batch_id,
            pipeline_name,
            trigger_type,
        )
    )

def mark_pipeline_run_success(
    batch_id,
    rows_extracted,
    rows_landed,
    cursor,
):
    query = """
        UPDATE metadata.pipeline_runs
        SET
            status = 'SUCCESS',
            finished_at = CURRENT_TIMESTAMP,
            rows_extracted = %s,
            rows_landed = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = %s;
    """

    cursor.execute(
        query,
        (
            rows_extracted,
            rows_landed,
            batch_id,
        ),
    )

def mark_pipeline_run_failed(
    batch_id,
    error_message,
    cursor,
):
    query = """
        UPDATE metadata.pipeline_runs
        SET
            status = 'FAILED',
            finished_at = CURRENT_TIMESTAMP,
            error_message = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = %s;
    """

    cursor.execute(
        query,
        (
            error_message,
            batch_id,
        ),
    )

def get_latest_pipeline_run(pipeline_name, cursor):
    query = """
        SELECT
            batch_id,
            status
        FROM metadata.pipeline_runs
        WHERE pipeline_name = %s
        ORDER BY started_at DESC
        LIMIT 1;
    """

    cursor.execute(query, (pipeline_name,))

    row = cursor.fetchone()

    if row is None:
        return None

    return row

def resume_pipeline_run(batch_id, cursor):
    query = """
        UPDATE metadata.pipeline_runs
        SET
            status = 'STARTED',
            finished_at = NULL,
            error_message = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE batch_id = %s;
    """

    cursor.execute(query, (batch_id,))

if __name__ == "__main__":
    conn = None
    cursor = None

    try:
        conn = get_warehouse_connection()
        cursor = conn.cursor()

        batch_id, status = get_latest_pipeline_run("core_transactions_ingestion", cursor)
        print(batch_id)
        print(status)

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()