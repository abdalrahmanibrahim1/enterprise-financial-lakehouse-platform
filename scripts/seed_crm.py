from generate_crm_data import generate_crm_dataset
from test_connections import get_crm_connection

def seed_crm_segments(cursor, segments):
    for segment in segments:
        cursor.execute(
            """
            INSERT INTO crm_segments (segment_id, segment_name, risk_band, updated_at)
            VALUES (%s, %s, %s, %s);
            """,
            (
                segment["segment_id"],
                segment["segment_name"],
                segment["risk_band"],
                segment["updated_at"],
            )
        )

def seed_crm_customers(cursor, customers):
    for customer in customers:
        cursor.execute(
            """
            INSERT INTO crm_customers (customer_id, national_id, full_name, birth_date, city, gender, segment_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s,%s, %s, %s, %s, %s);
            """,
            (
                customer["customer_id"],
                customer["national_id"],
                customer["full_name"],
                customer["birth_date"],
                customer["city"],
                customer["gender"],
                customer["segment_id"],
                customer["created_at"],
                customer["updated_at"],
            )
        )

def seed_crm_contacts(cursor, contacts):
    for contact in contacts:
        cursor.execute(
            """
            INSERT INTO crm_contacts (contact_id, customer_id, contact_type, contact_value, is_primary, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                contact["contact_id"],
                contact["customer_id"],
                contact["contact_type"],
                contact["contact_value"],
                contact["is_primary"],
                contact["created_at"],
                contact["updated_at"]
            )
        )

def seed_crm_customer_status_history(cursor, statuses):
    for status in statuses:
        cursor.execute(
            """
            INSERT INTO crm_customer_status_history (status_history_id, customer_id, status, valid_from, valid_to, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                status["status_history_id"],
                status["customer_id"],
                status["status"],
                status["valid_from"],
                status["valid_to"],
                status["updated_at"],
            )
        )

def seed_crm():
    conn = None
    cursor = None

    try:
        conn = get_crm_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM crm_customer_status_history;")
        cursor.execute("DELETE FROM crm_contacts;")
        cursor.execute("DELETE FROM crm_customers;")
        cursor.execute("DELETE FROM crm_segments;")

        crm_dataset = generate_crm_dataset(1000)

        seed_crm_segments(cursor, crm_dataset["segments"])
        seed_crm_customers(cursor, crm_dataset["customers"])
        seed_crm_contacts(cursor, crm_dataset["contacts"])
        seed_crm_customer_status_history(cursor, crm_dataset["status_history"])

        conn.commit()

        print("CRM seed completed successfully")
        print(f"Segments inserted: {len(crm_dataset['segments'])}")
        print(f"Customers inserted: {len(crm_dataset['customers'])}")
        print(f"Contacts inserted: {len(crm_dataset['contacts'])}")
        print(f"Status history rows inserted: {len(crm_dataset['status_history'])}")

    except Exception:
        if conn is not None:
            conn.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    seed_crm()
