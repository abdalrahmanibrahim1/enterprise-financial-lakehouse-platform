from src.connectors.mysql_connector import get_crm_connection
from src.connectors.postgres_connector import (
    get_core_connection,
    get_warehouse_connection,
)
from src.connectors.minio_connector import (
    ensure_bucket_exists,
    get_minio_client,
    upload_file_to_minio,
    object_exists,
    download_file_from_minio,
    list_objects,
)

from src.utils.lake_paths import(
    build_lake_object_key
)

from pathlib import Path

if __name__ == "__main__":
    conn = get_core_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"Core PostgreSQL connection successful: {result}")
    cursor.close()
    conn.close()

    conn = get_warehouse_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"Warehouse PostgreSQL connection successful: {result}")
    cursor.close()
    conn.close()

    conn = get_crm_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"CRM MySQL connection successful: {result}")
    cursor.close()
    conn.close()

    minio_client = get_minio_client()

    ensure_bucket_exists()

    response = minio_client.list_buckets()

    bucket_names = [
        bucket["Name"]
        for bucket in response["Buckets"]
    ]

    print(
        f"MinIO connection successful. "
        f"Buckets found: {bucket_names}"
    )


    PROJECT_ROOT = Path(__file__).resolve().parent

    tmp_dir = PROJECT_ROOT / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    test_file_path = tmp_dir / "minio_test.txt"
    test_file_path.write_text(
        "Hello from MinIO",
        encoding="utf-8",
    )

    

    test_object_key = build_lake_object_key(
        "test",
        "minio",
        "connection",
        "manual",
        "minio_test.txt",
    )

    uploaded_object_key = upload_file_to_minio(
        str(test_file_path),
        test_object_key,
    )

    print(f"Uploaded MinIO object: {uploaded_object_key}")

    exists = object_exists(test_object_key)
    print(f"Uploaded object exists: {exists}")

    downloaded_file_path = tmp_dir /"minio_test_downloaded.txt"
    download_file_from_minio(
        test_object_key,
        downloaded_file_path
    )

    original_content = test_file_path.read_text(encoding="utf-8")
    downloaded_content = downloaded_file_path.read_text(encoding="utf-8")

    print(original_content == downloaded_content)


    objects = list_objects("test/minio/")

    print(f"Objects found: {objects}")

    print(object_exists(test_object_key))
    print(object_exists("this/object/does/not/exist.txt"))