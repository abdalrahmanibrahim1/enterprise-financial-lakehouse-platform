import csv
from pathlib import Path

from psycopg2.extras import RealDictCursor

from src.connectors.postgres_connector import get_core_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "source"
    / "card_processor"
    / "cards"
    / "cc_cards.csv"
)

CARD_CSV_FIELDS = [
    "card_id",
    "account_id",
    "customer_id",
    "card_network",
    "masked_pan",
    "card_status",
    "billing_currency",
    "issued_at",
]

REQUIRED_CARD_FIELDS = set(CARD_CSV_FIELDS)

VALID_CARD_NETWORKS = {
    "VISA",
    "MASTERCARD",
}


def fetch_credit_card_accounts(core_cursor):
    query = """
        SELECT
            account_id,
            customer_id,
            account_status,
            currency,
            account_open_date
        FROM core_accounts
        WHERE product_id = 'PRD007'
        ORDER BY account_id;
    """

    core_cursor.execute(query)
    return core_cursor.fetchall()


def build_card_records(card_accounts):
    card_records = []

    for account in card_accounts:
        account_id = account["account_id"]

        account_number = int(
            account_id.replace("ACC", "", 1)
        )

        card_id = account_id.replace(
            "ACC",
            "CARD",
            1,
        )

        card_network = (
            "VISA"
            if account_number % 2 == 0
            else "MASTERCARD"
        )

        last_four = f"{account_number % 10000:04d}"
        masked_pan = f"**** **** **** {last_four}"

        card_record = {
            "card_id": card_id,
            "account_id": account_id,
            "customer_id": account["customer_id"],
            "card_network": card_network,
            "masked_pan": masked_pan,
            "card_status": account["account_status"],
            "billing_currency": account["currency"],
            "issued_at": account["account_open_date"],
        }

        card_records.append(card_record)

    return card_records


def audit_card_records(card_accounts, card_records):
    errors = 0

    card_ids = [
        card["card_id"]
        for card in card_records
    ]

    generated_account_ids = [
        card["account_id"]
        for card in card_records
    ]

    source_account_ids = {
        account["account_id"]
        for account in card_accounts
    }

    # One card record should exist for every credit-card account.
    if len(card_records) != len(card_accounts):
        errors += 1

    # Every generated card ID must be unique.
    if len(card_ids) != len(set(card_ids)):
        errors += 1

    # Every Core account should appear only once.
    if len(generated_account_ids) != len(
        set(generated_account_ids)
    ):
        errors += 1

    # Generated records must cover the exact same Core accounts.
    if set(generated_account_ids) != source_account_ids:
        errors += 1

    for card in card_records:
        card_fields = set(card.keys())

        # Reject missing or unexpected fields.
        if card_fields != REQUIRED_CARD_FIELDS:
            errors += 1
            continue

        # Required fields must contain values.
        if any(
            card[field] is None
            for field in REQUIRED_CARD_FIELDS
        ):
            errors += 1

        if card["card_network"] not in VALID_CARD_NETWORKS:
            errors += 1

        masked_pan = card["masked_pan"]

        valid_masked_pan = (
            isinstance(masked_pan, str)
            and masked_pan.startswith("**** **** **** ")
            and len(masked_pan) == 19
            and masked_pan[-4:].isdigit()
        )

        if not valid_masked_pan:
            errors += 1

    print(f"Card records checked: {len(card_records)}")
    print(f"Card record errors: {errors}")

    if errors == 0:
        print("No card record errors found")

    return errors


def write_card_records_csv(card_records, output_path):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CARD_CSV_FIELDS,
        )

        writer.writeheader()
        writer.writerows(card_records)

    print(f"Card CSV written: {output_path}")
    print(f"Rows written: {len(card_records)}")


def serialize_card_records(card_records):
    serialized_records = []

    for card in card_records:
        serialized_record = {
            field: str(card[field])
            for field in CARD_CSV_FIELDS
        }

        serialized_records.append(serialized_record)

    return serialized_records


def verify_card_csv(output_path, card_records):
    errors = 0

    if not output_path.is_file():
        print(f"Card CSV does not exist: {output_path}")
        return 1

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        headers = reader.fieldnames
        rows = list(reader)

    if headers != CARD_CSV_FIELDS:
        errors += 1
        print(f"Invalid CSV headers: {headers}")
        print(f"Expected CSV headers: {CARD_CSV_FIELDS}")

    if len(rows) != len(card_records):
        errors += 1
        print(f"CSV row count: {len(rows)}")
        print(f"Expected row count: {len(card_records)}")

    expected_rows = serialize_card_records(card_records)

    if rows != expected_rows:
        errors += 1
        print("CSV contents do not match generated card records")

    print(f"CSV records checked: {len(rows)}")
    print(f"CSV verification errors: {errors}")

    if errors == 0:
        print("No CSV verification errors found")

    return errors


def generate_card_master():
    core_conn = None

    try:
        core_conn = get_core_connection()

        with core_conn.cursor(
            cursor_factory=RealDictCursor
        ) as core_cursor:
            card_accounts = fetch_credit_card_accounts(
                core_cursor
            )

        print(
            f"Credit-card accounts found: "
            f"{len(card_accounts)}"
        )

        card_records = build_card_records(
            card_accounts
        )

        print(
            f"Card records generated: "
            f"{len(card_records)}"
        )

        audit_errors = audit_card_records(
            card_accounts,
            card_records,
        )

        if audit_errors > 0:
            raise ValueError(
                "Card record audit failed; "
                "the CSV was not written"
            )

        write_card_records_csv(
            card_records,
            OUTPUT_PATH,
        )

        verification_errors = verify_card_csv(
            OUTPUT_PATH,
            card_records,
        )

        if verification_errors > 0:
            raise ValueError(
                "Card CSV verification failed"
            )

        print("Card master generation completed successfully")

    finally:
        if core_conn is not None:
            core_conn.close()


if __name__ == "__main__":
    generate_card_master()