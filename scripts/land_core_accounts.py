from pathlib import Path
from datetime import datetime

from src.connectors.postgres_connector import (
    get_core_connection,
    get_metadata_connection,
)
from src.landing.local_file_landing import land_local_file
from src.metadata.pipeline_runs import (
    create_pipeline_run,
    get_latest_pipeline_run,
    mark_pipeline_run_failed,
    mark_pipeline_run_success,
    resume_pipeline_run,
)
from src.metadata.pipeline_watermarks import (
    deserialize_watermark,
    get_watermark,
    serialize_watermark,
    upsert_watermark,
)
from src.utils.csv_utils import write_rows_to_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_NAME = "core_accounts_ingestion"

LANDING_CSV_PATH = (
    PROJECT_ROOT
    / "tmp"
    / "landing"
    / "core"
    / "core_accounts.csv"
)

def fetch_core_accounts(cursor, watermark_value):
    if watermark_value is None:
        query = """
            SELECT *
            FROM core_accounts
            ORDER BY updated_at, account_id;
        """

        cursor.execute(query)
    else:
        watermark = deserialize_watermark(watermark_value)

        updated_at = datetime.fromisoformat(
            watermark["updated_at"]
        )
        account_id = watermark["account_id"]

        query = """
            SELECT *
            FROM core_accounts
            WHERE (updated_at, account_id) > (%s, %s)
            ORDER BY updated_at, account_id;
        """

        cursor.execute(
            query,
            (
                updated_at,
                account_id,
            ),
        )

    column_names = [
        description[0]
        for description in cursor.description
    ]

    rows = cursor.fetchall()

    return column_names, rows

if __name__ == "__main__":
    core_conn = None
    core_cursor = None
    metadata_conn = None
    metadata_cursor = None
    batch_id = None

    try:
        core_conn = get_core_connection()
        core_cursor = core_conn.cursor()

        metadata_conn = get_metadata_connection()
        metadata_cursor = metadata_conn.cursor()

        latest_run = get_latest_pipeline_run(
            PIPELINE_NAME,
            metadata_cursor
        )

        if latest_run is not None and latest_run[1] in ("FAILED", "STARTED"):
            batch_id = latest_run[0]

            resume_pipeline_run(
                batch_id = batch_id,
                cursor= metadata_cursor
            )

            metadata_conn.commit()

            print(f"Pipeline run resumed: {batch_id}")

        else:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            create_pipeline_run(
                batch_id=batch_id,
                pipeline_name=PIPELINE_NAME,
                trigger_type="manual",
                cursor=metadata_cursor
            )

            metadata_conn.commit()

            print(f"Pipeline run started: {batch_id}")

        watermark_value = get_watermark(
            "core",
            "core_accounts",
            metadata_cursor
        )
     
        column_names, accounts = fetch_core_accounts(
            core_cursor,
            watermark_value
        )

        print(f"Watermark: {watermark_value}")
        print(f"Rows extracted: {len(accounts)}")

        if not accounts:
            mark_pipeline_run_success(
                batch_id=batch_id,
                rows_extracted=len(accounts),
                rows_landed=len(accounts),
                cursor=metadata_cursor
            )

            metadata_conn.commit()

            print(f"Pipeline run completed with no new rows: {batch_id}")

        else:
            output_path = write_rows_to_csv(
                column_names,
                accounts,
                LANDING_CSV_PATH
            )

            print(f"Landing CSV: {output_path}")

            object_key, file_id = land_local_file(
                batch_id=batch_id,
                local_path=output_path,
                source_system="core",
                dataset_name="accounts",
                row_count=len(accounts),
                cursor=metadata_cursor
            )

            print(f"Landed object: {object_key}")
            print(f"Registry file ID: {file_id}")

            updated_at_index = column_names.index("updated_at")
            accounts_id_index = column_names.index("account_id")

            last_account = accounts[-1]

            last_updated_at = last_account[updated_at_index]
            last_account_id = last_account[accounts_id_index]

            new_watermark_value = serialize_watermark(
                updated_at = last_updated_at,
                account_id = last_account_id
            )

            upsert_watermark(
                source_system="core",
                source_table="core_accounts",
                watermark_column="updated_at,account_id",
                last_watermark_value = new_watermark_value,
                last_successful_batch=batch_id,
                cursor=metadata_cursor
            )
            
            mark_pipeline_run_success(
                batch_id=batch_id,
                rows_extracted=len(accounts),
                rows_landed=len(accounts),
                cursor=metadata_cursor
            )

            metadata_conn.commit()

            print(f"Watermark updated: {new_watermark_value}")
            print(f"Pipeline run completed successfully: {batch_id}")

    except Exception as exc:
        if metadata_conn is not None:
            metadata_conn.rollback()

        if batch_id is not None and metadata_cursor is not None:
            mark_pipeline_run_failed(
                batch_id=batch_id,
                error_message=str(exc),
                cursor=metadata_cursor,
            )

            metadata_conn.commit()

        raise

    finally:
        if core_cursor is not None:
            core_cursor.close()
        if core_conn is not None:
            core_conn.close()

        if metadata_cursor is not None:
            metadata_cursor.close()
        if metadata_conn is not None:
            metadata_conn.close()

