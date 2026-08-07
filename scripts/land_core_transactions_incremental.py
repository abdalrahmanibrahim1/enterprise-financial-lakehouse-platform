from src.metadata.pipeline_watermarks import deserialize_watermark
from src.connectors.postgres_connector import (
    get_core_connection,
    get_warehouse_connection,
)
from src.metadata.pipeline_watermarks import get_watermark
from src.metadata.pipeline_watermarks import (
    get_watermark,
    serialize_watermark,
    upsert_watermark,
)

def fetch_core_transactions(cursor, watermark_value):
    if watermark_value is None:
        query = """
            SELECT *
            FROM core_transactions
            ORDER BY created_at, transaction_id;
        """

        cursor.execute(query)

    else:
        created_at, transaction_id = deserialize_watermark(watermark_value)

        query = """
            SELECT *
            FROM core_transactions
            WHERE (created_at, transaction_id) > (%s, %s)
            ORDER BY created_at, transaction_id;
        """

        cursor.execute(query, (created_at, transaction_id))

    column_names = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    return column_names, rows

if __name__ == "__main__":
    core_conn = None
    core_cursor = None
    warehouse_conn = None
    warehouse_cursor = None

    try:
        core_conn = get_core_connection()
        core_cursor = core_conn.cursor()

        warehouse_conn = get_warehouse_connection()
        warehouse_cursor = warehouse_conn.cursor()

        watermark_value = get_watermark(
            "core",
            "core_transactions",
            warehouse_cursor,
        )

        column_names, transactions = fetch_core_transactions(
            core_cursor,
            watermark_value,
        )

        print(f"Watermark: {watermark_value}")
        print(f"Rows extracted: {len(transactions)}")
            
    finally:
        if core_cursor is not None:
            core_cursor.close()
        if core_conn is not None:
            core_conn.close()

        if warehouse_cursor is not None:
            warehouse_cursor.close()
        if warehouse_conn is not None:
            warehouse_conn.close()