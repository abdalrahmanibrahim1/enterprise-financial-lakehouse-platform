from datetime import datetime
from pathlib import Path
import json
from src.landing.local_file_landing import land_local_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    fx_path = (
        PROJECT_ROOT
        / "data"
        / "source"
        / "reference"
        / "ref_fx_rates.json"
    )

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