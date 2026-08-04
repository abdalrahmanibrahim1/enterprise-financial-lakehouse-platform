from datetime import datetime

from src.landing.local_file_landing import land_local_file


if __name__ == "__main__":
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    object_key, file_id = land_local_file(
        local_path="data/source/card_processor/cards/cc_cards.csv",
        source_system="card_processor",
        dataset_name="cards",
        batch_id=batch_id,
    )

    print(f"Landed object: {object_key}")
    print(f"Registry file ID: {file_id}")
