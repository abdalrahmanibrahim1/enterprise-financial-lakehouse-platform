from src.connectors.mysql_connector import get_crm_connection
from src.connectors.postgres_connector import get_core_connection
from psycopg2.extras import execute_values
import pymysql

from scripts.generate_core_data import (
    generate_core_dataset,
    audit_accounts_summary,
    audit_transactions_summary,
    clean_accounts_for_output,
)

def fetch_crm_customers():
    """Fetch CRM customers fields needed for Core account generation."""
    crm_conn = None
    crm_cursor = None

    try:
        crm_conn = get_crm_connection()
        crm_cursor = crm_conn.cursor(pymysql.cursors.DictCursor)

        crm_cursor.execute(
            """
            SELECT
                customer_id,
                city,
                segment_id,
                created_at
            FROM crm_customers;
            """
        )

        return crm_cursor.fetchall()

    finally:
        if crm_cursor is not None:
            crm_cursor.close()

        if crm_conn is not None:
            crm_conn.close()

def seed_core_branches(cursor, branches):
    if not branches:
        return
    
    execute_values(
        cursor,
        """
        INSERT INTO core_branches (
            branch_id,
            branch_name,
            city,
            updated_at
        )
        VALUES %s;
        """,
        [
            (
                branch["branch_id"],
                branch["branch_name"],
                branch["city"],
                branch["updated_at"],
            )
            for branch in branches
        ]
    )

def seed_core_products(cursor, products):
    if not products:
        return

    execute_values(
        cursor,
        """
        INSERT INTO core_products (
            product_id,
            product_name,
            product_type,
            updated_at
        )
        VALUES %s;
        """,
        [
            (
                product["product_id"],
                product["product_name"],
                product["product_type"],
                product["updated_at"],
            )
            for product in products
        ]
    )

def seed_core_accounts(cursor, accounts):
    if not accounts:
        return

    execute_values(
        cursor,
        """
        INSERT INTO core_accounts (
            account_id,
            customer_id,
            branch_id,
            product_id,
            account_open_date,
            account_status,
            currency,
            current_balance,
            created_at,
            updated_at
        )
        VALUES %s;
        """,
        [
            (
                account["account_id"],
                account["customer_id"],
                account["branch_id"],
                account["product_id"],
                account["account_open_date"],
                account["account_status"],
                account["currency"],
                account["current_balance"],
                account["created_at"],
                account["updated_at"],
            )
            for account in accounts
        ]
    )

def seed_core_transactions(cursor, transactions):
    if not transactions:
        return

    execute_values(
        cursor,
        """
        INSERT INTO core_transactions (
            transaction_id,
            account_id,
            transaction_timestamp,
            transaction_type,
            transaction_direction,
            amount,
            currency,
            channel,
            merchant_category,
            created_at
        )
        VALUES %s;
        """,
        [
            (
                transaction["transaction_id"],
                transaction["account_id"],
                transaction["transaction_timestamp"],
                transaction["transaction_type"],
                transaction["transaction_direction"],
                transaction["amount"],
                transaction["currency"],
                transaction["channel"],
                transaction["merchant_category"],
                transaction["created_at"],
            )
            for transaction in transactions
        ]
    )
    
def seed_core():
    core_conn = None
    core_cursor = None

    try:
        customers = fetch_crm_customers()

        if not customers:
            raise ValueError("No CRM customers found. Run seed_crm.py first.")

        core_dataset = generate_core_dataset(customers)

        audit_accounts_summary(
            core_dataset["accounts"],
            core_dataset["customers"],
            core_dataset["branches"],
            core_dataset["products"]
        )

        audit_transactions_summary(
            core_dataset["accounts"],
            core_dataset["transactions"]
        )

        accounts_for_insert = clean_accounts_for_output(
            core_dataset["accounts"]
        )

        core_conn = get_core_connection()
        core_cursor = core_conn.cursor()

        # Delete child tables first, then parent/reference tables.
        core_cursor.execute("DELETE FROM core_transactions;")
        core_cursor.execute("DELETE FROM core_accounts;")
        core_cursor.execute("DELETE FROM core_products;")
        core_cursor.execute("DELETE FROM core_branches;")

        seed_core_branches(
            core_cursor,
            core_dataset["branches"]
        )

        seed_core_products(
            core_cursor,
            core_dataset["products"]
        )

        seed_core_accounts(
            core_cursor,
            accounts_for_insert
        )

        seed_core_transactions(
            core_cursor,
            core_dataset["transactions"]
        )

        core_conn.commit()

        print("Core seed completed successfully")
        print(f"Branches inserted: {len(core_dataset['branches'])}")
        print(f"Products inserted: {len(core_dataset['products'])}")
        print(f"Accounts inserted: {len(accounts_for_insert)}")
        print(f"Transactions inserted: {len(core_dataset['transactions'])}")

    except Exception:
        if core_conn is not None:
            core_conn.rollback()

        raise

    finally:
        if core_cursor is not None:
            core_cursor.close()

        if core_conn is not None:
            core_conn.close()


if __name__ == "__main__":
    seed_core()    