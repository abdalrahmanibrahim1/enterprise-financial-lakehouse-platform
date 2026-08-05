from pathlib import Path

from src.connectors.minio_connector import upload_file_to_minio
from src.metadata.lake_file_registry import register_lake_file
from src.utils.lake_paths import build_lake_object_key

def land_local_file(
    local_path,
    source_system,
    dataset_name,
    batch_id,
    row_count = None
):
  
    file_path = Path(local_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    filename = file_path.name
    object_format = file_path.suffix.lstrip(".")

    object_key = build_lake_object_key(
        "landing",
        source_system,
        dataset_name,
        batch_id,
        filename
    )

    upload_file_to_minio(
        str(file_path),
        object_key
    )

    file_id = register_lake_file(
        batch_id=batch_id,
        zone="landing",
        object_key=object_key,
        object_format=object_format,
        source_system=source_system,
        dataset_name=dataset_name,
        row_count=row_count,
        file_size_bytes=file_path.stat().st_size,
        record_hash=None,
    )

    return object_key, file_id