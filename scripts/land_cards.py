import csv
from datetime import datetime
from pathlib import Path

from src.connectors.postgres_connector import get_metadata_connection
from src.landing.local_file_landing import land_local_file
from src.metadata.lake_file_registry import get_latest_content_hash
from src.utils.file_hashing import calculate_content_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    metadata_conn = None
    metadata_cursor = None

    try:
        cards_path = (
            PROJECT_ROOT
            / "data"
            / "source"
            / "card_processor"
            / "cards"
            / "cc_cards.csv"
        )

        metadata_conn = get_metadata_connection()
        metadata_cursor = metadata_conn.cursor()

        current_hash = calculate_content_hash(cards_path)

        latest_hash = get_latest_content_hash(
            source_system="card_processor",
            dataset_name="cards",
            cursor=metadata_cursor,
        )

        print(f"Current content hash: {current_hash}")
        print(f"Latest landed hash: {latest_hash}")

        if current_hash == latest_hash:
            print("cc_cards.csv is unchanged. Landing skipped.")

        else:
            with cards_path.open(
                mode="r",
                encoding="utf-8",
                newline="",
            ) as csv_file:
                reader = csv.reader(csv_file)
                next(reader, None)
                row_count = sum(1 for row in reader)

            batch_id = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            object_key, file_id = land_local_file(
                local_path=cards_path,
                source_system="card_processor",
                dataset_name="cards",
                batch_id=batch_id,
                row_count=row_count,
            )

            print(f"Rows landed: {row_count}")
            print(f"Landed object: {object_key}")
            print(f"Registry file ID: {file_id}")

    finally:
        if metadata_cursor is not None:
            metadata_cursor.close()

        if metadata_conn is not None:
            metadata_conn.close()