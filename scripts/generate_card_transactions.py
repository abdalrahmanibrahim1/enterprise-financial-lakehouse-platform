from psycopg2.extras import RealDictCursor

from src.connectors.postgres_connector import get_core_connection

import random

from decimal import Decimal, ROUND_HALF_UP

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

if __name__ == "__main__":
    core_conn = None

    try:
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

        print("\nFirst two transactions:")

        for transaction in transactions[:2]:
            print(transaction)
        
        processor_records = build_base_processor_records(
            transactions
        )

        print(
            f"Base processor records generated: "
            f"{len(processor_records)}"
        )

        for record in processor_records[:2]:
            print(record)

        audit_errors = audit_base_processor_records(
            transactions,
            processor_records,
        )

        if audit_errors > 0:
            raise ValueError("Base processor record audit failed")


        processor_records_98, missing_records = (
            apply_missing_processor_records(
                processor_records
            )
        )

        match_rate = (
            len(processor_records_98)
            / len(processor_records)
            * 100
        )

        print(
            f"Processor records retained: "
            f"{len(processor_records_98)}"
        )
        print(
            f"Intentionally missing records: "
            f"{len(missing_records)}"
        )
        print(f"Resulting match rate: {match_rate:.2f}%")

        split_errors = audit_missing_processor_records(
            processor_records,
            processor_records_98,
            missing_records,
        )

        if split_errors > 0:
            raise ValueError("Processor missing-record split audit failed")
        
        (
            processor_records_with_amount_mismatches,
            amount_mismatch_details,
        ) = apply_amount_mismatches(
            processor_records_98,
            len(processor_records),
        )

        print(
            f"Intentional amount mismatches: "
            f"{len(amount_mismatch_details)}"
        )

        print("\nFirst two amount mismatches:")

        for mismatch in amount_mismatch_details[:2]:
            print(mismatch)

        expected_amount_mismatch_count = round(
            len(processor_records) * 0.005
        )

        amount_mismatch_errors = audit_amount_mismatches(
            processor_records_98,
            processor_records_with_amount_mismatches,
            amount_mismatch_details,
            expected_amount_mismatch_count,
        )

        if amount_mismatch_errors > 0:
            raise ValueError("Amount-mismatch audit failed")

    finally:
        if core_conn is not None:
            core_conn.close()