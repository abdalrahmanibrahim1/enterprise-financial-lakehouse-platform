import json
from datetime import datetime

from src.connectors.postgres_connector import get_metadata_connection

def get_watermark(source_system, source_table, cursor):
    query = """
        SELECT last_watermark_value
        FROM metadata.pipeline_watermarks
        WHERE source_system = %s
        AND source_table = %s;
    """

    cursor.execute(query, (source_system, source_table))

    row = cursor.fetchone()

    if row is None:
        return None

    return row[0]

def upsert_watermark(
    source_system,
    source_table,
    watermark_column,
    last_watermark_value,
    last_successful_batch,
    cursor,
):
    query = """
    INSERT INTO metadata.pipeline_watermarks (
        source_system,
        source_table,
        watermark_column,
        last_watermark_value,
        last_successful_batch
    )
    VALUES (%s, %s, %s, %s, %s)

    ON CONFLICT (source_system, source_table)
    DO UPDATE SET
        watermark_column = EXCLUDED.watermark_column,
        last_watermark_value = EXCLUDED.last_watermark_value,
        last_successful_batch = EXCLUDED.last_successful_batch,
        updated_at = CURRENT_TIMESTAMP;
    """

    cursor.execute(
        query,
        (
            source_system,
            source_table,
            watermark_column,
            last_watermark_value,
            last_successful_batch,
         )
    )

def serialize_watermark(**values):
    serialized_values = {}

    for key, value in values.items():
        if isinstance(value, datetime):
            serialized_values[key] = value.isoformat()
        else:
            serialized_values[key] = value

    return json.dumps(serialized_values)

def deserialize_watermark(last_watermark_value):
    return json.loads(last_watermark_value)

if __name__ == "__main__":
    conn = None
    cursor = None

    try:
        conn = get_metadata_connection()
        cursor = conn.cursor()

        source_system = "core"
        source_table = "core_transactions"

        watermark = get_watermark(
            source_system,
            source_table,
            cursor,
        )

        print(f"Current watermark: {watermark}")

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

