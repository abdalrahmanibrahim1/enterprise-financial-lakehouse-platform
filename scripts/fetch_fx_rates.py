from src.connectors.postgres_connector import get_core_connection

import requests
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FX_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "source"
    / "reference"
    / "fx_rates.json"
)

def fetch_fx_requirements(core_cursor):
    query = """
    SELECT
        currency,
        MIN(transaction_timestamp)::date AS start_date,
        MAX(transaction_timestamp)::date AS end_date
    FROM core_transactions
    WHERE currency <> 'JOD'
    GROUP BY currency
    ORDER BY currency;
    """

    core_cursor.execute(query)

    return core_cursor.fetchall()

def fetch_fx_rates(base_currency, start_date, end_date):
    url = "https://api.frankfurter.dev/v2/rates"
    params = {
        "base": base_currency,
        "quotes": "JOD",
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    rates = response.json()

    return rates

def write_fx_rates(rates, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(
            rates,
            json_file,
            indent = 2,
            ensure_ascii=False
        )

def verify_fx_rates_file(expected_rates, output_path):
    with output_path.open("r", encoding="utf-8") as json_file:
        loaded_rates = json.load(json_file)

    print(f"Expected records: {len(expected_rates)}")
    print(f"Loaded records: {len(loaded_rates)}")
    print(f"Exact content match: {loaded_rates == expected_rates}")

    if loaded_rates != expected_rates:
        raise ValueError("FX rates file verification failed")

if __name__ == "__main__":
    fx_requirements = None
    conn = None

    try:
        conn = get_core_connection()
        with conn.cursor() as core_cursor:
            fx_requirements = fetch_fx_requirements(core_cursor)
    finally:
        if conn is not None:
            conn.close()

    if not fx_requirements:
        raise ValueError("No non-JOD transaction currencies found in Core") 

    all_rates = []

    for row in fx_requirements:
        currency, start_date,end_date = row
        rates = fetch_fx_rates(currency, start_date, end_date)
        if not rates:
            raise ValueError(
                f"No FX rates returned for {currency} "
                f"between {start_date} and {end_date}"
            )
        
        all_rates.extend(rates)

    write_fx_rates(all_rates, FX_OUTPUT_PATH)
    verify_fx_rates_file(all_rates, FX_OUTPUT_PATH)

    print(f"Written: {FX_OUTPUT_PATH}")
    print(f"Records written: {len(all_rates)}")


    
