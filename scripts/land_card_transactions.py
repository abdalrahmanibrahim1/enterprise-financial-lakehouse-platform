import csv
from pathlib import Path
from datetime import datetime

from src.landing.local_file_landing import land_local_file
from src.connectors.postgres_connector import get_metadata_connection
from src.metadata.lake_file_registry import get_landed_file_hashes
from src.utils.file_hashing import calculate_content_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]

transactions_dir = (
    PROJECT_ROOT
    / "data"
    / "source"
    / "card_processor"
    / "transactions"
)

transaction_files = sorted(
    transactions_dir.glob("*.csv")
)

if __name__ == "__main__":
    metadata_conn = None
    metadata_cursor = None
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        metadata_conn = get_metadata_connection()
        metadata_cursor = metadata_conn.cursor()

        landed_hashes = get_landed_file_hashes(
            source_system="card_processor",
            dataset_name="transactions",
            cursor=metadata_cursor,
        )

        for file_path in transaction_files:
            file_name = file_path.name
            current_hash = calculate_content_hash(file_path)

            if (
                file_name in landed_hashes
                and current_hash == landed_hashes[file_name]
            ):
                print(f"Skipped unchanged file: {file_name}")
                continue

            with file_path.open(
                mode="r",
                encoding="utf-8",
                newline="",
            ) as csv_file:
                reader = csv.reader(csv_file)
                next(reader, None)
                row_count = sum(1 for row in reader)

            object_key, file_id = land_local_file(
                local_path=file_path,
                source_system="card_processor",
                dataset_name="transactions",
                batch_id=batch_id,
                row_count=row_count,
            )

            print(f"Landed object: {object_key}")
            print(f"Registry file ID: {file_id}")

    finally:
        if metadata_cursor is not None:
            metadata_cursor.close()

        if metadata_conn is not None:
            metadata_conn.close()