from pathlib import Path
from datetime import datetime

from src.connectors.postgres_connector import (
    get_core_connection,
    get_warehouse_connection,
)
from src.landing.local_file_landing import land_local_file
from src.metadata.pipeline_watermarks import (
    deserialize_watermark,
    get_watermark,
    serialize_watermark,
    upsert_watermark,
)
from src.utils.csv_utils import write_rows_to_csv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LANDING_CSV_PATH = (
    PROJECT_ROOT
    / "tmp"
    / "landing"
    / "core"
    / "core_transactions.csv"
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

        if transactions:
            output_path = write_rows_to_csv(
                column_names,
                transactions,
                LANDING_CSV_PATH,
            )

            print(f"Landing CSV: {output_path}")

            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            object_key, file_id = land_local_file(
                local_path=output_path,
                source_system="core",
                dataset_name="transactions",
                batch_id=batch_id,
                row_count=len(transactions),
            )

            print(f"Landed object: {object_key}")
            print(f"Registry file ID: {file_id}")

            created_at_index = column_names.index("created_at")
            transaction_id_index = column_names.index("transaction_id")

            last_transaction = transactions[-1]

            last_created_at = last_transaction[created_at_index]
            last_transaction_id = last_transaction[transaction_id_index]

            new_watermark_value = serialize_watermark(
                last_created_at,
                last_transaction_id,
            )

            upsert_watermark(
                source_system="core",
                source_table="core_transactions",
                watermark_column="created_at,transaction_id",
                last_watermark_value=new_watermark_value,
                last_successful_batch=batch_id,
                cursor=warehouse_cursor,
            )

            warehouse_conn.commit()

            print(f"Watermark updated: {new_watermark_value}")
    finally:
        if core_cursor is not None:
            core_cursor.close()
        if core_conn is not None:
            core_conn.close()

        if warehouse_cursor is not None:
            warehouse_cursor.close()
        if warehouse_conn is not None:
            warehouse_conn.close()