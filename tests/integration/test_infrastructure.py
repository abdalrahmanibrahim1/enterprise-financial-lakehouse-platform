from uuid import uuid4

from src.connectors.mysql_connector import get_crm_connection
from src.connectors.postgres_connector import (
    get_core_connection,
    get_metadata_connection,
)
from src.connectors.minio_connector import (
    ensure_bucket_exists,
    get_minio_client,
    upload_file_to_minio,
    object_exists,
    download_file_from_minio,
    list_objects,
)
from src.metadata.lake_file_registry import register_lake_file
from src.utils.lake_paths import build_lake_object_key


def test_core_postgres_connection():
    conn = get_core_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        assert result == (1,)

    finally:
        cursor.close()
        conn.close()


def test_metadata_postgres_connection():
    conn = get_metadata_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        assert result == (1,)

    finally:
        cursor.close()
        conn.close()


def test_crm_mysql_connection():
    conn = get_crm_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        assert result == (1,)

    finally:
        cursor.close()
        conn.close()


def test_minio_connection():
    ensure_bucket_exists()

    client = get_minio_client()
    response = client.list_buckets()

    bucket_names = [
        bucket["Name"]
        for bucket in response["Buckets"]
    ]

    assert len(bucket_names) > 0


def test_minio_file_round_trip(tmp_path):
    client = get_minio_client()

    bucket_name = ensure_bucket_exists()

    test_id = uuid4().hex

    local_file = tmp_path / "minio_test.txt"
    downloaded_file = tmp_path / "minio_test_downloaded.txt"

    local_file.write_text(
        "Hello from MinIO",
        encoding="utf-8",
    )

    object_key = build_lake_object_key(
        "test",
        "integration",
        "minio",
        test_id,
        "minio_test.txt",
    )

    try:
        uploaded_key = upload_file_to_minio(
            str(local_file),
            object_key,
        )

        assert uploaded_key == object_key
        assert object_exists(object_key) is True

        download_file_from_minio(
            object_key,
            downloaded_file,
        )

        assert downloaded_file.read_text(
            encoding="utf-8"
        ) == local_file.read_text(
            encoding="utf-8"
        )

        objects = list_objects(
            f"test/integration/minio/batch_id={test_id}/"
        )

        assert object_key in objects

    finally:
        client.delete_object(
            Bucket=bucket_name,
            Key=object_key,
        )


def test_missing_minio_object_returns_false():
    missing_key = (
        f"test/integration/missing/"
        f"{uuid4().hex}.txt"
    )

    assert object_exists(missing_key) is False


def test_lake_file_registry_insert_can_rollback():
    conn = get_metadata_connection()
    cursor = conn.cursor()

    test_id = uuid4().hex
    batch_id = f"test_{test_id}"

    object_key = build_lake_object_key(
        "test",
        "integration",
        "registry",
        batch_id,
        "registry_test.txt",
    )

    try:
        file_id = register_lake_file(
            batch_id=batch_id,
            zone="test",
            object_key=object_key,
            object_format="txt",
            source_system="integration_test",
            dataset_name="registry_test",
            row_count=1,
            file_size_bytes=10,
            content_hash="test_hash",
            cursor=cursor,
        )

        assert file_id is not None

        cursor.execute(
            """
            SELECT
                batch_id,
                zone,
                object_key,
                source_system,
                dataset_name
            FROM metadata.lake_file_registry
            WHERE file_id = %s;
            """,
            (file_id,),
        )

        row = cursor.fetchone()

        assert row == (
            batch_id,
            "test",
            object_key,
            "integration_test",
            "registry_test",
        )

    finally:
        # register_lake_file received our cursor, so it did
        # not commit. Rolling back removes the test row.
        conn.rollback()
        cursor.close()
        conn.close()