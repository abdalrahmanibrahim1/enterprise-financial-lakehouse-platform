from pathlib import Path
from datetime import datetime

from src.landing.local_file_landing import land_local_file
from src.connectors.postgres_connector import get_core_connection
from src.utils.csv_utils import write_rows_to_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def identify_tables(cursor):
    query="""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name <> 'core_transactions'
            AND table_name <> 'core_accounts'
        ORDER BY table_name;
    """
    cursor.execute(query)

    return [
        row[0]
        for row in cursor.fetchall()
    ]

def read_table(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name};")

    column_names = [
        column[0]
        for column in cursor.description
    ]

    rows = cursor.fetchall()

    return column_names, rows

def export_table_to_csv(cursor, table_name, output_path):
    column_names, rows = read_table(cursor, table_name)

    output_path = write_rows_to_csv(
        column_names,
        rows,
        output_path,
    )

    return output_path, len(rows)

if __name__ == "__main__":
    conn = None
    cursor = None

    try:
        conn = get_core_connection()
        cursor = conn.cursor()

        tables = identify_tables(cursor)
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        for table_name in tables:
            output_path = (
                PROJECT_ROOT
                / "tmp"
                / "landing"
                / "core"
                / f"{table_name}.csv"
            )

            output_path, row_count = export_table_to_csv(
                cursor,
                table_name,
                output_path,
            )

            print(f"Exported file: {output_path}")
            print(f"Exported rows: {row_count}")

            dataset_name = table_name.removeprefix("core_")

            object_key, file_id = land_local_file(
                local_path=output_path,
                source_system="core",
                dataset_name=dataset_name,
                batch_id=batch_id,
                row_count=row_count,
            )

            print(f"Landed object: {object_key}")
            print(f"Registry file ID: {file_id}")



        
    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()