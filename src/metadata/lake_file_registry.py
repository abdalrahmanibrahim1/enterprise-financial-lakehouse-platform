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
):
    conn = None
    cursor = None
    try:
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
        conn.commit()

        return file_id
    
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()   