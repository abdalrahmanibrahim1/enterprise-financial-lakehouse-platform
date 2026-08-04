from pathlib import Path
import csv
from src.landing.local_file_landing import land_local_file
from datetime import datetime

transactions_dir = Path(
    "data/source/card_processor/transactions"
)

transaction_files = sorted(
    transactions_dir.glob("*.csv")
)

if __name__ == "__main__":
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    for file_path in transaction_files:
        with file_path.open(
            mode="r",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            reader = csv.reader(csv_file)

            next(reader, None)  # Skip the header
            row_count = sum(1 for row in reader)


        object_key, file_id = land_local_file(
            local_path=file_path,
            source_system="card_processor",
            dataset_name="transactions",
            batch_id=batch_id,
            row_count=row_count
        )

        print(f"Landed object: {object_key}")
        print(f"Registry file ID: {file_id}")