from datetime import datetime
from pathlib import Path
import csv
from src.landing.local_file_landing import land_local_file


if __name__ == "__main__":
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    cards_path = Path(
        "data/source/card_processor/cards/cc_cards.csv"
    )

    with cards_path.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)
        row_count = sum(1 for row in reader)

    object_key, file_id = land_local_file(
        local_path=cards_path,
        source_system="card_processor",
        dataset_name="cards",
        batch_id=batch_id,
        row_count=row_count,
    )

    print(f"Landed object: {object_key}")
    print(f"Registry file ID: {file_id}")
