from psycopg2.extras import RealDictCursor

from src.connectors.postgres_connector import get_core_connection

import random

from decimal import Decimal, ROUND_HALF_UP

from collections import defaultdict

import csv
from pathlib import Path

MERCHANT_NAMES_BY_CATEGORY = {
    "Groceries": ["Hypermax", "Safeway", "Cozmo"],
    "Restaurants": ["Almonds Coffee House", "Shawerma Reem", "Buffalo Wings"],
    "Fuel": ["Manaseer", "JoPetrol", "TotalEnergies"],
    "Retail": ["City Mall Store", "SmartBuy", "DNA"],
    "Travel": ["Royal Jordanian", "Booking.com", "Wizz Air"],
    "Telecom": ["Zain", "Orange", "Umniah"],
    "Healthcare": ["Pharmacy One", "MedLabs", "Biolab"],
    "Education": ["Udemy", "Coursera", "University Bookshop"],
    "Entertainment": ["Prime Cinemas", "Netflix", "PlayStation Network"],
    "Hotels": ["Amman Rotana", "Le Royal", "Marriott"],
    "Subscriptions": ["Spotify", "YouTube Premium", "Microsoft 365"],
    "Online Services": ["Amazon Web Services", "Google Services", "OpenAI"],
    "Clothing": ["Zara", "H&M", "American Eagle"],
    "Electronics": ["SmartBuy", "Leaders Center", "iSystem"],
}


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRANSACTION_OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "source"
    / "card_processor"
    / "transactions"
)

PROCESSOR_TRANSACTION_FIELDS = [
    "processor_transaction_id",
    "card_id",
    "customer_id",
    "transaction_timestamp",
    "transaction_type",
    "merchant_name",
    "amount",
    "currency",
    "merchant_category",
    "auth_status",
]

def fetch_posted_card_transactions(core_cursor):
    query = """
        SELECT 
            t.transaction_id,
                t.account_id,
                a.customer_id,
                t.transaction_timestamp,
                t.transaction_type,
                t.amount,
                t.currency,
                t.merchant_category,
                t.channel,
                t.created_at
        FROM core_transactions t
        JOIN core_accounts a
            ON t.account_id = a.account_id
        WHERE a.product_id = 'PRD007'
            AND t.transaction_type IN (
                'Card Purchase', 
                'Cash Advance'
            )
            ORDER BY 
                t.transaction_timestamp,
                t.transaction_id;
    """

    core_cursor.execute(query)
    return core_cursor.fetchall()

def build_base_processor_record(transaction, random_generator):
    processor_transaction_id = transaction["transaction_id"].replace(
        "TR",
        "PTX",
        1,
    )

    card_id = transaction["account_id"].replace(
        "ACC",
        "CARD",
        1,
    )

    transaction_type = (
        "PURCHASE"
        if transaction["transaction_type"] == "Card Purchase"
        else "CASH_ADVANCE"
    )

    if transaction["transaction_type"] == "Cash Advance":
        merchant_name = "ATM Network"
    else:
        merchant_name = random_generator.choice(
            MERCHANT_NAMES_BY_CATEGORY[
                transaction["merchant_category"]
            ]
        )

    return {
        "processor_transaction_id": processor_transaction_id,
        "card_id": card_id,
        "customer_id": transaction["customer_id"],
        "transaction_timestamp": transaction["transaction_timestamp"],
        "transaction_type": transaction_type,
        "merchant_name": merchant_name,
        "amount": transaction["amount"],
        "currency": transaction["currency"],
        "merchant_category": transaction["merchant_category"],
        "auth_status": "APPROVED",
    }

def build_base_processor_records(transactions, seed = 42):
    random_generator = random.Random(seed)
    processor_records = []

    for transaction in transactions:
        processor_record = build_base_processor_record(
            transaction,
            random_generator
        )
        processor_records.append(processor_record)

    return processor_records

def audit_base_processor_records(transactions, processor_records):
    errors = 0

    processor_ids = [
        record["processor_transaction_id"]
        for record in processor_records
    ]

    if len(processor_records) != len(transactions):
        errors += 1

    if len(processor_ids) != len(set(processor_ids)):
        errors += 1

    required_fields = {
        "processor_transaction_id",
        "card_id",
        "customer_id",
        "transaction_timestamp",
        "transaction_type",
        "merchant_name",
        "amount",
        "currency",
        "merchant_category",
        "auth_status",
    }

    valid_transaction_types = {
        "PURCHASE",
        "CASH_ADVANCE",
    }

    for record in processor_records:
        if set(record.keys()) != required_fields:
            errors += 1
            continue

        required_non_nullable = required_fields - {
            "merchant_category"
        }

        if any(
            record[field] is None
            for field in required_non_nullable
        ):
            errors += 1

        if record["transaction_type"] not in valid_transaction_types:
            errors += 1

        if record["auth_status"] != "APPROVED":
            errors += 1

        if record["amount"] <= 0:
            errors += 1

        if (
            record["transaction_type"] == "PURCHASE"
            and record["merchant_category"] is None
        ):
            errors += 1

        if (
            record["transaction_type"] == "CASH_ADVANCE"
            and record["merchant_category"] is not None
        ):
            errors += 1

    print(f"Base processor records checked: {len(processor_records)}")
    print(f"Base processor record errors: {errors}")

    if errors == 0:
        print("No base processor record errors found")

    return errors

def apply_missing_processor_records(
    processor_records,
    missing_rate=0.01,
    seed=42,
):
    random_generator = random.Random(seed)

    missing_count = round(
        len(processor_records) * missing_rate
    )

    missing_processor_ids = {
        record["processor_transaction_id"]
        for record in random_generator.sample(
            processor_records,
            missing_count,
        )
    }

    retained_records = [
        record
        for record in processor_records
        if record["processor_transaction_id"]
        not in missing_processor_ids
    ]

    missing_records = [
        record
        for record in processor_records
        if record["processor_transaction_id"]
        in missing_processor_ids
    ]

    return retained_records, missing_records

def audit_missing_processor_records(
    base_records,
    retained_records,
    missing_records,
):
    errors = 0

    base_ids = {
        record["processor_transaction_id"]
        for record in base_records
    }

    retained_ids = {
        record["processor_transaction_id"]
        for record in retained_records
    }

    missing_ids = {
        record["processor_transaction_id"]
        for record in missing_records
    }

    # Every original record must end up in exactly one group.
    if retained_ids | missing_ids != base_ids:
        errors += 1

    # No record may be both retained and missing.
    if retained_ids & missing_ids:
        errors += 1

    # The two group sizes must reconstruct the original count.
    if len(retained_records) + len(missing_records) != len(base_records):
        errors += 1

    match_rate = len(retained_records) / len(base_records)

    # Allow minor rounding around the intended 98%.
    if not 0.989 <= match_rate <= 0.991:
        errors += 1

    print(f"Missing-record split errors: {errors}")

    if errors == 0:
        print("Missing-record split is valid")

    return errors

def apply_amount_mismatches(
    retained_records,
    base_record_count,
    mismatch_rate=0.005,
    seed=43,
):
    random_generator = random.Random(seed)

    mismatch_count = round(
        base_record_count * mismatch_rate
    )

    selected_ids = {
        record["processor_transaction_id"]
        for record in random_generator.sample(
            retained_records,
            mismatch_count,
        )
    }

    adjustment_factors = [
        Decimal("0.98"),
        Decimal("0.99"),
        Decimal("1.01"),
        Decimal("1.02"),
    ]

    updated_records = []
    mismatch_details = []

    for record in retained_records:
        updated_record = record.copy()

        if (
            record["processor_transaction_id"]
            in selected_ids
        ):
            original_amount = record["amount"]

            adjustment_factor = random_generator.choice(
                adjustment_factors
            )

            mismatched_amount = (
                original_amount * adjustment_factor
            ).quantize(
                Decimal("0.001"),
                rounding=ROUND_HALF_UP,
            )

            updated_record["amount"] = mismatched_amount

            mismatch_details.append({
                "processor_transaction_id":
                    record["processor_transaction_id"],
                "original_amount": original_amount,
                "mismatched_amount": mismatched_amount,
            })

        updated_records.append(updated_record)

    return updated_records, mismatch_details

def audit_amount_mismatches(
    retained_records,
    updated_records,
    mismatch_details,
    expected_count,
):
    errors = 0

    if len(updated_records) != len(retained_records):
        errors += 1

    if len(mismatch_details) != expected_count:
        errors += 1

    original_by_id = {
        record["processor_transaction_id"]: record
        for record in retained_records
    }

    updated_by_id = {
        record["processor_transaction_id"]: record
        for record in updated_records
    }

    mismatch_ids = {
        detail["processor_transaction_id"]
        for detail in mismatch_details
    }

    if set(original_by_id) != set(updated_by_id):
        errors += 1

    for processor_id in original_by_id:
        original_record = original_by_id[processor_id]
        updated_record = updated_by_id[processor_id]

        if processor_id in mismatch_ids:
            if updated_record["amount"] == original_record["amount"]:
                errors += 1
        else:
            if updated_record != original_record:
                errors += 1

    print(f"Amount-mismatch audit errors: {errors}")

    if errors == 0:
        print("Amount-mismatch population is valid")

    return errors

from datetime import timedelta


def apply_timestamp_mismatches(
    retained_records,
    amount_mismatch_details,
    base_record_count,
    mismatch_rate=0.005,
    seed=44,
):
    random_generator = random.Random(seed)

    amount_mismatch_ids = {
        detail["processor_transaction_id"]
        for detail in amount_mismatch_details
    }

    eligible_records = [
        record
        for record in retained_records
        if record["processor_transaction_id"]
        not in amount_mismatch_ids
    ]

    mismatch_count = round(
        base_record_count * mismatch_rate
    )

    selected_ids = {
        record["processor_transaction_id"]
        for record in random_generator.sample(
            eligible_records,
            mismatch_count,
        )
    }

    updated_records = []
    timestamp_mismatch_details = []

    for record in retained_records:
        updated_record = record.copy()

        if (
            record["processor_transaction_id"]
            in selected_ids
        ):
            original_timestamp = record[
                "transaction_timestamp"
            ]

            shift_minutes = random_generator.choice(
                [2, 5, 10, 15]
            )

            mismatched_timestamp = (
                original_timestamp
                + timedelta(minutes=shift_minutes)
            )

            updated_record["transaction_timestamp"] = (
                mismatched_timestamp
            )

            timestamp_mismatch_details.append({
                "processor_transaction_id":
                    record["processor_transaction_id"],
                "original_timestamp":
                    original_timestamp,
                "mismatched_timestamp":
                    mismatched_timestamp,
            })

        updated_records.append(updated_record)

    return updated_records, timestamp_mismatch_details

def audit_timestamp_mismatches(
    records_before_timestamp,
    updated_records,
    timestamp_mismatch_details,
    amount_mismatch_details,
    expected_count,
):
    errors = 0

    before_by_id = {
        record["processor_transaction_id"]: record
        for record in records_before_timestamp
    }

    updated_by_id = {
        record["processor_transaction_id"]: record
        for record in updated_records
    }

    timestamp_details_by_id = {
        detail["processor_transaction_id"]: detail
        for detail in timestamp_mismatch_details
    }

    amount_mismatch_ids = {
        detail["processor_transaction_id"]
        for detail in amount_mismatch_details
    }

    timestamp_mismatch_ids = set(
        timestamp_details_by_id
    )

    # Record count must remain unchanged.
    if len(updated_records) != len(records_before_timestamp):
        errors += 1

    # No duplicate IDs should exist.
    if len(updated_by_id) != len(updated_records):
        errors += 1

    # The same transaction IDs must exist before and after.
    if set(before_by_id) != set(updated_by_id):
        errors += 1

    # Confirm the intended number of timestamp mismatches.
    if len(timestamp_mismatch_details) != expected_count:
        errors += 1

    # Details must not contain duplicate transaction IDs.
    if (
        len(timestamp_details_by_id)
        != len(timestamp_mismatch_details)
    ):
        errors += 1

    # Amount and timestamp mismatches must be separate.
    if timestamp_mismatch_ids & amount_mismatch_ids:
        errors += 1

    for processor_id, before_record in before_by_id.items():
        updated_record = updated_by_id[processor_id]

        if processor_id in timestamp_mismatch_ids:
            detail = timestamp_details_by_id[processor_id]

            original_timestamp = before_record[
                "transaction_timestamp"
            ]

            mismatched_timestamp = updated_record[
                "transaction_timestamp"
            ]

            if (
                detail["original_timestamp"]
                != original_timestamp
            ):
                errors += 1

            if (
                detail["mismatched_timestamp"]
                != mismatched_timestamp
            ):
                errors += 1

            # The timestamp must actually change.
            if mismatched_timestamp == original_timestamp:
                errors += 1

            # Keep the transaction in the same monthly file.
            if (
                mismatched_timestamp.year
                != original_timestamp.year
                or mismatched_timestamp.month
                != original_timestamp.month
            ):
                errors += 1

            # No field other than the timestamp may change.
            before_without_timestamp = {
                field: value
                for field, value in before_record.items()
                if field != "transaction_timestamp"
            }

            updated_without_timestamp = {
                field: value
                for field, value in updated_record.items()
                if field != "transaction_timestamp"
            }

            if (
                before_without_timestamp
                != updated_without_timestamp
            ):
                errors += 1

        else:
            # Non-selected records must remain identical.
            if updated_record != before_record:
                errors += 1

    print(f"Timestamp-mismatch audit errors: {errors}")

    if errors == 0:
        print("Timestamp-mismatch population is valid")

    return errors

def generate_card_transactions():
    core_conn = None

    try:
        # --------------------------------------------------
        # 1. Fetch posted card transactions from Core
        # --------------------------------------------------
        core_conn = get_core_connection()

        with core_conn.cursor(
            cursor_factory=RealDictCursor
        ) as core_cursor:
            transactions = fetch_posted_card_transactions(
                core_cursor
            )

        purchase_count = sum(
            transaction["transaction_type"] == "Card Purchase"
            for transaction in transactions
        )

        cash_advance_count = sum(
            transaction["transaction_type"] == "Cash Advance"
            for transaction in transactions
        )

        print(
            f"Posted card transactions found: "
            f"{len(transactions)}"
        )
        print(f"Card Purchases: {purchase_count}")
        print(f"Cash Advances: {cash_advance_count}")

        print("\nFirst two Core transactions:")

        for transaction in transactions[:2]:
            print(transaction)

        # --------------------------------------------------
        # 2. Build clean processor records
        # --------------------------------------------------
        processor_records = build_base_processor_records(
            transactions
        )

        print(
            f"\nBase processor records generated: "
            f"{len(processor_records)}"
        )

        print("\nFirst two processor records:")

        for record in processor_records[:2]:
            print(record)

        base_audit_errors = audit_base_processor_records(
            transactions,
            processor_records,
        )

        if base_audit_errors > 0:
            raise ValueError(
                "Base processor record audit failed"
            )

        # --------------------------------------------------
        # 3. Remove 1% of processor records
        # --------------------------------------------------
        (
            retained_processor_records,
            missing_records,
        ) = apply_missing_processor_records(
            processor_records
        )

        retained_rate = (
            len(retained_processor_records)
            / len(processor_records)
            * 100
        )

        print(
            f"\nProcessor records retained: "
            f"{len(retained_processor_records)}"
        )
        print(
            f"Intentionally missing records: "
            f"{len(missing_records)}"
        )
        print(
            f"Resulting retained rate: "
            f"{retained_rate:.2f}%"
        )

        split_errors = audit_missing_processor_records(
            processor_records,
            retained_processor_records,
            missing_records,
        )

        if split_errors > 0:
            raise ValueError(
                "Processor missing-record split audit failed"
            )

        # --------------------------------------------------
        # 4. Add 0.5% amount mismatches
        # --------------------------------------------------
        (
            processor_records_with_amount_mismatches,
            amount_mismatch_details,
        ) = apply_amount_mismatches(
            retained_processor_records,
            len(processor_records),
        )

        print(
            f"\nIntentional amount mismatches: "
            f"{len(amount_mismatch_details)}"
        )

        print("\nFirst two amount mismatches:")

        for mismatch in amount_mismatch_details[:2]:
            print(mismatch)

        expected_amount_mismatch_count = round(
            len(processor_records) * 0.005
        )

        amount_mismatch_errors = audit_amount_mismatches(
            retained_processor_records,
            processor_records_with_amount_mismatches,
            amount_mismatch_details,
            expected_amount_mismatch_count,
        )

        if amount_mismatch_errors > 0:
            raise ValueError(
                "Amount-mismatch audit failed"
            )

        # --------------------------------------------------
        # 5. Add 0.5% timestamp mismatches
        # --------------------------------------------------
        (
            final_processor_records,
            timestamp_mismatch_details,
        ) = apply_timestamp_mismatches(
            processor_records_with_amount_mismatches,
            amount_mismatch_details,
            len(processor_records),
        )

        print(
            f"\nIntentional timestamp mismatches: "
            f"{len(timestamp_mismatch_details)}"
        )

        print("\nFirst two timestamp mismatches:")

        for mismatch in timestamp_mismatch_details[:2]:
            print(mismatch)

        expected_timestamp_mismatch_count = round(
            len(processor_records) * 0.005
        )

        timestamp_mismatch_errors = (
            audit_timestamp_mismatches(
                processor_records_with_amount_mismatches,
                final_processor_records,
                timestamp_mismatch_details,
                amount_mismatch_details,
                expected_timestamp_mismatch_count,
            )
        )

        if timestamp_mismatch_errors > 0:
            raise ValueError(
                "Timestamp-mismatch audit failed"
            )

        # --------------------------------------------------
        # 6. Add processor-only declined/reversed records
        # --------------------------------------------------
        (
            all_processor_records,
            processor_only_records,
        ) = add_processor_only_records(
            final_processor_records,
            processor_records,
            len(processor_records),
        )

        expected_declined_count = round(
            len(processor_records) * 0.01
        )

        expected_reversed_count = round(
            len(processor_records) * 0.002
        )

        processor_only_errors = audit_processor_only_records(
            processor_records,
            final_processor_records,
            all_processor_records,
            processor_only_records,
            expected_declined_count,
            expected_reversed_count,
        )

        if processor_only_errors > 0:
            raise ValueError(
                "Processor-only record audit failed"
            )

        declined_count = sum(
            record["auth_status"] == "DECLINED"
            for record in processor_only_records
        )

        reversed_count = sum(
            record["auth_status"] == "REVERSED"
            for record in processor_only_records
        )

        print(
            f"\nProcessor-only records: "
            f"{len(processor_only_records)}"
        )
        print(
            f"Processor-only declined: "
            f"{declined_count}"
        )
        print(
            f"Processor-only reversed: "
            f"{reversed_count}"
        )

        print("\nFirst two processor-only records:")

        for record in processor_only_records[:2]:
            print(record)

        # --------------------------------------------------
        # 7. Group processor records by month
        # --------------------------------------------------
        monthly_processor_records = (
            group_processor_records_by_month(
                all_processor_records
            )
        )

        monthly_grouping_errors = (
            audit_monthly_processor_groups(
                all_processor_records,
                monthly_processor_records,
            )
        )

        if monthly_grouping_errors > 0:
            raise ValueError(
                "Monthly processor grouping audit failed"
            )

        print("\nMonthly processor groups:")

        for (year, month), records in (
            monthly_processor_records.items()
        ):
            print(
                f"{year}-{month:02d}: "
                f"{len(records)} records"
            )

        written_files = write_monthly_processor_csvs(
            monthly_processor_records,
            TRANSACTION_OUTPUT_DIR,
        )

        print(
            f"\nMonthly CSV files written: "
            f"{len(written_files)}"
        )
        # --------------------------------------------------
        # 8. Print reconciliation summary
        # --------------------------------------------------
        exact_match_count = (
            len(processor_records)
            - len(missing_records)
            - len(amount_mismatch_details)
            - len(timestamp_mismatch_details)
        )

        exact_match_rate = (
            exact_match_count
            / len(processor_records)
            * 100
        )

        print("\nCard processor generation summary:")

        print(
            f"Core posted transactions: "
            f"{len(processor_records)}"
        )
        print(
            f"Exact matches: "
            f"{exact_match_count}"
        )
        print(
            f"Missing from processor: "
            f"{len(missing_records)}"
        )
        print(
            f"Amount mismatches: "
            f"{len(amount_mismatch_details)}"
        )
        print(
            f"Timestamp mismatches: "
            f"{len(timestamp_mismatch_details)}"
        )
        print(
            f"Exact-match rate: "
            f"{exact_match_rate:.2f}%"
        )
        print(
            f"Core-derived processor records: "
            f"{len(final_processor_records)}"
        )
        print(
            f"Processor-only records: "
            f"{len(processor_only_records)}"
        )
        print(
            f"Total processor records: "
            f"{len(all_processor_records)}"
        )

    finally:
        if core_conn is not None:
            core_conn.close()


def add_processor_only_records(
    current_processor_records,
    base_processor_records,
    base_record_count,
    declined_rate=0.01,
    reversed_rate=0.002,
    seed=45,
):
    random_generator = random.Random(seed)

    if not current_processor_records:
        raise ValueError(
            "Cannot generate processor-only records "
            "from an empty processor population"
        )

    if not base_processor_records:
        raise ValueError(
            "Base processor records cannot be empty"
        )

    declined_count = round(
        base_record_count * declined_rate
    )

    reversed_count = round(
        base_record_count * reversed_rate
    )

    existing_id_numbers = [
        int(
            record["processor_transaction_id"].replace(
                "PTX",
                "",
                1,
            )
        )
        for record in base_processor_records
    ]

    next_id_number = max(existing_id_numbers) + 1

    statuses = (
        ["DECLINED"] * declined_count
        + ["REVERSED"] * reversed_count
    )

    random_generator.shuffle(statuses)

    processor_only_records = []

    for status in statuses:
        template_record = random_generator.choice(
            current_processor_records
        )

        new_record = template_record.copy()

        new_record["processor_transaction_id"] = (
            f"PTX{next_id_number:06d}"
        )

        new_record["auth_status"] = status

        new_record["transaction_timestamp"] = (
            template_record["transaction_timestamp"]
            + timedelta(
                minutes=random_generator.randint(
                    1,
                    30,
                )
            )
        )

        new_record["amount"] = (
            Decimal(
                random_generator.randint(
                    1000,
                    5_000_000,
                )
            )
            / Decimal("1000")
        ).quantize(
            Decimal("0.001")
        )

        processor_only_records.append(new_record)

        next_id_number += 1

    combined_records = (
        current_processor_records
        + processor_only_records
    )

    return combined_records, processor_only_records

def audit_processor_only_records(
    base_processor_records,
    final_processor_records,
    all_processor_records,
    processor_only_records,
    expected_declined_count,
    expected_reversed_count,
):
    errors = 0

    base_ids = {
        record["processor_transaction_id"]
        for record in base_processor_records
    }

    final_ids = {
        record["processor_transaction_id"]
        for record in final_processor_records
    }

    processor_only_ids = {
        record["processor_transaction_id"]
        for record in processor_only_records
    }

    all_ids = [
        record["processor_transaction_id"]
        for record in all_processor_records
    ]

    declined_count = sum(
        record["auth_status"] == "DECLINED"
        for record in processor_only_records
    )

    reversed_count = sum(
        record["auth_status"] == "REVERSED"
        for record in processor_only_records
    )

    if len(all_processor_records) != (
        len(final_processor_records)
        + len(processor_only_records)
    ):
        errors += 1

    if len(all_ids) != len(set(all_ids)):
        errors += 1

    # Processor-only IDs must not match any Core-derived ID,
    # including intentionally missing records.
    if processor_only_ids & base_ids:
        errors += 1

    if final_ids & processor_only_ids:
        errors += 1

    if declined_count != expected_declined_count:
        errors += 1

    if reversed_count != expected_reversed_count:
        errors += 1

    valid_statuses = {
        "DECLINED",
        "REVERSED",
    }

    for record in processor_only_records:
        if record["auth_status"] not in valid_statuses:
            errors += 1

        if record["amount"] <= 0:
            errors += 1

        if record["transaction_timestamp"] is None:
            errors += 1

    print(f"Processor-only audit errors: {errors}")

    if errors == 0:
        print("Processor-only population is valid")

    return errors

def group_processor_records_by_month(processor_records):
    monthly_records = defaultdict(list) 

    for record in processor_records:
        transaction_timestamp = record[
            "transaction_timestamp"
        ]

        month_key = (
            transaction_timestamp.year,
            transaction_timestamp.month,
        )

        monthly_records[month_key].append(record)

    return dict(
        sorted(monthly_records.items())
    )

def audit_monthly_processor_groups(
    processor_records,
    monthly_records,
):
    errors = 0

    original_ids = [
        record["processor_transaction_id"]
        for record in processor_records
    ]

    grouped_records = [
        record
        for records in monthly_records.values()
        for record in records
    ]

    grouped_ids = [
        record["processor_transaction_id"]
        for record in grouped_records
    ]

    # Grouping must preserve the total record count.
    if len(grouped_records) != len(processor_records):
        errors += 1

    # The same exact transaction IDs must exist after grouping.
    if set(grouped_ids) != set(original_ids):
        errors += 1

    # Grouping must not introduce duplicate IDs.
    if len(grouped_ids) != len(set(grouped_ids)):
        errors += 1

    # Every record must belong to its group's year and month.
    for (year, month), records in monthly_records.items():
        for record in records:
            timestamp = record["transaction_timestamp"]

            if (
                timestamp.year != year
                or timestamp.month != month
            ):
                errors += 1

    print(
        f"Monthly groups checked: "
        f"{len(monthly_records)}"
    )
    print(
        f"Records across monthly groups: "
        f"{len(grouped_records)}"
    )
    print(
        f"Monthly grouping errors: "
        f"{errors}"
    )

    if errors == 0:
        print("Monthly processor grouping is valid")

    return errors

def write_monthly_processor_csvs(
    monthly_records,
    output_dir,
):
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    written_files = []

    for (year, month), records in monthly_records.items():
        output_path = (
            output_dir
            / f"cc_card_transactions_{year}_{month:02d}.csv"
        )

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=PROCESSOR_TRANSACTION_FIELDS,
            )

            writer.writeheader()
            writer.writerows(records)

        written_files.append(output_path)

        print(
            f"Written: {output_path.name} "
            f"({len(records)} records)"
        )

    return written_files

if __name__ == "__main__":
    generate_card_transactions()