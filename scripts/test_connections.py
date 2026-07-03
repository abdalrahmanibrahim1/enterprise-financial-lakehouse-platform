from src.connectors.mysql_connector import get_crm_connection
from src.connectors.postgres_connector import (
    get_core_connection,
    get_warehouse_connection,
)

if __name__ == "__main__":
    conn = get_core_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"Core PostgreSQL connection successful: {result}")
    cursor.close()
    conn.close()

    conn = get_warehouse_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"Warehouse PostgreSQL connection successful: {result}")
    cursor.close()
    conn.close()

    conn = get_crm_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"CRM MySQL connection successful: {result}")
    cursor.close()
    conn.close()