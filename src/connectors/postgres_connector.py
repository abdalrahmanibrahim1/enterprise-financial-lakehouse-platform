import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


def get_core_connection():
    return psycopg2.connect(
        host=os.getenv("CORE_DB_HOST"),
        database=os.getenv("CORE_DB_NAME"),
        user=os.getenv("CORE_DB_USER"),
        password=os.getenv("CORE_DB_PASSWORD"),
        port=os.getenv("CORE_DB_PORT"),
    )


def get_metadata_connection():
    return psycopg2.connect(
        host=os.getenv("METADATA_DB_HOST"),
        database=os.getenv("METADATA_DB_NAME"),
        user=os.getenv("METADATA_DB_USER"),
        password=os.getenv("METADATA_DB_PASSWORD"),
        port=os.getenv("METADATA_DB_PORT"),
    )