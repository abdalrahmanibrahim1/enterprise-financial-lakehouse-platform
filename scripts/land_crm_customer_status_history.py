from pathlib import Path
from datetime import datetime

from src.connectors.mysql_connector import get_crm_connection
from src.connectors.postgres_connector import get_metadata_connection

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

PIPELINE_NAME = "crm_customer_status_history_ingestion"

LANDING_CSV_PATH = (
    PROJECT_ROOT
    / "tmp"
    / "landing"
    / "crm"
    / "crm_customer_status_history.csv"
)


def fetch_crm_customer_status_history(
    cursor,
    watermark_value,
):
    if watermark_value is None:
        query = """
            SELECT *
            FROM crm_customer_status_history
            ORDER BY updated_at, status_history_id;
        """

        cursor.execute(query)

    else:
        watermark = deserialize_watermark(
            watermark_value
        )

        updated_at = datetime.fromisoformat(
            watermark["updated_at"]
        )
        status_history_id = watermark[
            "status_history_id"
        ]

        query = """
            SELECT *
            FROM crm_customer_status_history
            WHERE (updated_at, status_history_id) > (%s, %s)
            ORDER BY updated_at, status_history_id;
        """

        cursor.execute(
            query,
            (
                updated_at,
                status_history_id,
            ),
        )

    column_names = [
        description[0]
        for description in cursor.description
    ]

    rows = cursor.fetchall()

    return column_names, rows


if __name__ == "__main__":
    crm_conn = None
    crm_cursor = None

    metadata_conn = None
    metadata_cursor = None

    batch_id = None

    try:
        crm_conn = get_crm_connection()
        crm_cursor = crm_conn.cursor()

        metadata_conn = get_metadata_connection()
        metadata_cursor = metadata_conn.cursor()

        latest_run = get_latest_pipeline_run(
            PIPELINE_NAME,
            metadata_cursor,
        )

        if (
            latest_run is not None
            and latest_run[1] in ("STARTED", "FAILED")
        ):
            batch_id = latest_run[0]

            resume_pipeline_run(
                batch_id=batch_id,
                cursor=metadata_cursor,
            )

            metadata_conn.commit()

            print(
                f"Pipeline run resumed: {batch_id}"
            )

        else:
            batch_id = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            create_pipeline_run(
                batch_id=batch_id,
                pipeline_name=PIPELINE_NAME,
                trigger_type="manual",
                cursor=metadata_cursor,
            )

            metadata_conn.commit()

            print(
                f"Pipeline run started: {batch_id}"
            )

        watermark_value = get_watermark(
            source_system="crm",
            source_table="crm_customer_status_history",
            cursor=metadata_cursor,
        )

        (
            column_names,
            status_history_rows,
        ) = fetch_crm_customer_status_history(
            crm_cursor,
            watermark_value,
        )

        print(f"Watermark: {watermark_value}")
        print(
            f"Rows extracted: "
            f"{len(status_history_rows)}"
        )

        if not status_history_rows:
            mark_pipeline_run_success(
                batch_id=batch_id,
                rows_extracted=0,
                rows_landed=0,
                cursor=metadata_cursor,
            )

            metadata_conn.commit()

            print(
                f"Pipeline run completed with no new rows: "
                f"{batch_id}"
            )

        else:
            output_path = write_rows_to_csv(
                column_names,
                status_history_rows,
                LANDING_CSV_PATH,
            )

            print(
                f"Landing CSV: {output_path}"
            )

            object_key, file_id = land_local_file(
                local_path=output_path,
                source_system="crm",
                dataset_name="customer_status_history",
                batch_id=batch_id,
                row_count=len(status_history_rows),
                cursor=metadata_cursor,
            )

            print(
                f"Landed object: {object_key}"
            )
            print(
                f"Registry file ID: {file_id}"
            )

            updated_at_index = column_names.index(
                "updated_at"
            )
            status_history_id_index = (
                column_names.index(
                    "status_history_id"
                )
            )

            last_status_history_row = (
                status_history_rows[-1]
            )

            last_updated_at = (
                last_status_history_row[
                    updated_at_index
                ]
            )
            last_status_history_id = (
                last_status_history_row[
                    status_history_id_index
                ]
            )

            new_watermark_value = (
                serialize_watermark(
                    updated_at=last_updated_at,
                    status_history_id=(
                        last_status_history_id
                    ),
                )
            )

            upsert_watermark(
                source_system="crm",
                source_table=(
                    "crm_customer_status_history"
                ),
                watermark_column=(
                    "updated_at,status_history_id"
                ),
                last_watermark_value=(
                    new_watermark_value
                ),
                last_successful_batch=batch_id,
                cursor=metadata_cursor,
            )

            mark_pipeline_run_success(
                batch_id=batch_id,
                rows_extracted=(
                    len(status_history_rows)
                ),
                rows_landed=(
                    len(status_history_rows)
                ),
                cursor=metadata_cursor,
            )

            metadata_conn.commit()

            print(
                f"Watermark updated: "
                f"{new_watermark_value}"
            )
            print(
                f"Pipeline run completed successfully: "
                f"{batch_id}"
            )

    except Exception as exc:
        if metadata_conn is not None:
            metadata_conn.rollback()

        if (
            batch_id is not None
            and metadata_cursor is not None
            and metadata_conn is not None
        ):
            mark_pipeline_run_failed(
                batch_id=batch_id,
                error_message=str(exc),
                cursor=metadata_cursor,
            )

            metadata_conn.commit()

        raise

    finally:
        if crm_cursor is not None:
            crm_cursor.close()

        if crm_conn is not None:
            crm_conn.close()

        if metadata_cursor is not None:
            metadata_cursor.close()

        if metadata_conn is not None:
            metadata_conn.close()