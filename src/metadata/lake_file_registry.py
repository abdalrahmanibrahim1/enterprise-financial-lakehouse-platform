from src.connectors.postgres_connector import get_warehouse_connection


def register_lake_file(
    batch_id,
    zone,
    object_key,
    object_format,
    source_system,
    dataset_name,
    row_count=None,
    file_size_bytes=None,
    content_hash=None,
    cursor=None,
):
    conn = None
    owns_connection = cursor is None

    try:
        if owns_connection:
            conn = get_warehouse_connection()
            cursor = conn.cursor()

        query = """
            INSERT INTO metadata.lake_file_registry (
                batch_id,
                zone,
                object_key,
                object_format,
                source_system,
                dataset_name,
                row_count,
                file_size_bytes,
                content_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING file_id
        """

        cursor.execute(
            query,
            (
                batch_id,
                zone,
                object_key,
                object_format,
                source_system,
                dataset_name,
                row_count,
                file_size_bytes,
                content_hash,
            ),
        )

        file_id = cursor.fetchone()[0]

        if owns_connection:
            conn.commit()

        return file_id

    except Exception:
        if owns_connection and conn is not None:
            conn.rollback()

        raise

    finally:
        if owns_connection:
            if cursor is not None:
                cursor.close()

            if conn is not None:
                conn.close()

def get_latest_content_hash(
    source_system,
    dataset_name,
    cursor
):
    query = """
        SELECT content_hash
        FROM metadata.lake_file_registry
        WHERE source_system = %s
            AND dataset_name = %s
            AND zone = 'landing'
        ORDER BY created_at DESC
        LIMIT 1;
    """

    cursor.execute(
        query,
        (
            source_system,
            dataset_name
        )
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return row[0]

def get_landed_file_hashes(
    source_system,
    dataset_name,
    cursor,
):
    query = """
        SELECT object_key, content_hash
        FROM metadata.lake_file_registry
        WHERE source_system = %s
          AND dataset_name = %s
          AND zone = 'landing'
        ORDER BY created_at DESC;
    """

    cursor.execute(
        query,
        (
            source_system,
            dataset_name,
        ),
    )

    rows = cursor.fetchall()

    file_hashes = {}

    for object_key, content_hash in rows:
        filename = object_key.rsplit("/", 1)[-1]

        if filename not in file_hashes:
            file_hashes[filename] = content_hash

    return file_hashes