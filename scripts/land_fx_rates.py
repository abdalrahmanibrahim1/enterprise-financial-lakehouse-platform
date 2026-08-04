from datetime import datetime

from src.landing.local_file_landing import land_local_file


if __name__ == "__main__":
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    object_key, file_id = land_local_file(
        local_path="data/source/reference/ref_fx_rates.json",
        source_system="reference",
        dataset_name="fx_rates",
        batch_id=batch_id,
    )

    print(f"Landed object: {object_key}")
    print(f"Registry file ID: {file_id}")