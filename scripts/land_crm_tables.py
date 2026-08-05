import csv
from pathlib import Path
from datetime import datetime

from src.landing.local_file_landing import land_local_file
from src.connectors.mysql_connector import get_crm_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def identify_tables(cursor):
    cursor.execute("SHOW TABLES;")

    return [
        row[0]
        for row in cursor.fetchall()
    ]

def read_table(cursor, table_name):
    cursor.execute(f"SELECT * FROM `{table_name}`;")

    column_names = [
        column[0]
        for column in cursor.description
    ]

    rows = cursor.fetchall()

    return column_names, rows

def export_table_to_csv(cursor, table_name, output_path):
    column_names, rows = read_table(cursor, table_name)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        mode="w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(column_names)
        writer.writerows(rows)

    return output_path, len(rows)

if __name__ == "__main__":
    conn = None
    cursor = None

    try:
        conn = get_crm_connection()
        cursor = conn.cursor()

        tables = identify_tables(cursor)
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        for table_name in tables:
            dataset_name = table_name.removeprefix("crm_")
        
            output_path = (
                PROJECT_ROOT
                / "tmp"
                / "landing"
                / "crm"
                / f"{table_name}.csv"
            )

            output_path, row_count = export_table_to_csv(
                cursor,
                table_name,
                output_path,
            )

            print(f"Exported file: {output_path}")
            print(f"Exported rows: {row_count}")

            object_key, file_id = land_local_file(
                local_path=output_path,
                source_system="crm",
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