import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

def get_crm_connection():
    conn = pymysql.connect(
        host = os.getenv("CRM_DB_HOST"),
        database = os.getenv("CRM_DB_NAME"),
        user = os.getenv("CRM_DB_USER"),
        password= os.getenv("CRM_DB_PASSWORD"),
        port = int(os.getenv("CRM_DB_PORT"))
    )

    return conn