from datetime import datetime
from pathlib import Path
import json

from src.landing.local_file_landing import land_local_file
from src.metadata.lake_file_registry import get_latest_content_hash
from src.connectors.postgres_connector import get_warehouse_connection
from src.utils.file_hashing import calculate_content_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    warehouse_conn = None
    warehouse_cursor = None

    try:
        warehouse_conn = get_warehouse_connection()
        warehouse_cursor = warehouse_conn.cursor()

        fx_path = (
            PROJECT_ROOT
            / "data"
            / "source"
            / "reference"
            / "ref_fx_rates.json"
        )

        current_hash = calculate_content_hash(fx_path)

        latest_hash = get_latest_content_hash(
            source_system="reference",
            dataset_name="fx_rates",
            cursor=warehouse_cursor,
        )

        if current_hash == latest_hash:
            print("ref_fx_rates.json is unchanged. Landing skipped.")

        else:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            with fx_path.open(
                mode="r",
                encoding="utf-8",
            ) as json_file:
                records = json.load(json_file)

            row_count = len(records)

            object_key, file_id = land_local_file(
                local_path=fx_path,
                source_system="reference",
                dataset_name="fx_rates",
                batch_id=batch_id,
                row_count=row_count,
            )

            print(f"Landed object: {object_key}")
            print(f"Registry file ID: {file_id}")

    finally:
        if warehouse_cursor is not None:
            warehouse_cursor.close()

        if warehouse_conn is not None:
            warehouse_conn.close()