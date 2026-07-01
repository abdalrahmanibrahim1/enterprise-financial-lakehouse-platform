import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path
import pymysql

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


def get_core_connection():
    conn = psycopg2.connect(
        host = os.getenv("CORE_DB_HOST"),
        database = os.getenv("CORE_DB_NAME"),
        user = os.getenv("CORE_DB_USER"),
        password= os.getenv("CORE_DB_PASSWORD"),
        port = os.getenv("CORE_DB_PORT")
    )

    return conn

def get_warehouse_connection():
    conn = psycopg2.connect(
        host = os.getenv("WAREHOUSE_DB_HOST"),
        database = os.getenv("WAREHOUSE_DB_NAME"),
        user = os.getenv("WAREHOUSE_DB_USER"),
        password= os.getenv("WAREHOUSE_DB_PASSWORD"),
        port = os.getenv("WAREHOUSE_DB_PORT")
    )

    return conn

def get_crm_connection():
    conn = pymysql.connect(
        host = os.getenv("CRM_DB_HOST"),
        database = os.getenv("CRM_DB_NAME"),
        user = os.getenv("CRM_DB_USER"),
        password= os.getenv("CRM_DB_PASSWORD"),
        port = int(os.getenv("CRM_DB_PORT"))
    )

    return conn    

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