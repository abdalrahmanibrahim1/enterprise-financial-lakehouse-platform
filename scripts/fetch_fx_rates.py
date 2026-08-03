from src.connectors.postgres_connector import get_core_connection

import requests
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REF_FX_RATES_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "source"
    / "reference"
    / "ref_fx_rates.json"
)

INVALID_RATE_INDEX = 0
INVALID_DATE_INDEX = 1

INVALID_RATE_VALUE = "NOT_A_NUMBER"
INVALID_DATE_VALUE = 12345

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

def inject_invalid_fx_types(rates):
    if len(rates) < 2:
        raise ValueError(
            "At least two FX records are required to inject invalid types"
        )

    # Copy the records so the untouched API response remains available.
    dirty_rates = [record.copy() for record in rates]

    dirty_rates[INVALID_RATE_INDEX]["rate"] = INVALID_RATE_VALUE
    dirty_rates[INVALID_DATE_INDEX]["date"] = INVALID_DATE_VALUE

    return dirty_rates

def verify_invalid_fx_types(output_path):
    with output_path.open("r", encoding="utf-8") as json_file:
        loaded_rates = json.load(json_file)

    invalid_rate = loaded_rates[INVALID_RATE_INDEX]["rate"]
    invalid_date = loaded_rates[INVALID_DATE_INDEX]["date"]

    if invalid_rate != INVALID_RATE_VALUE:
        raise ValueError("Invalid FX rate was not written correctly")

    if invalid_date != INVALID_DATE_VALUE:
        raise ValueError("Invalid FX date was not written correctly")

    if type(invalid_rate) is not str:
        raise TypeError("Injected FX rate must be a string")

    if type(invalid_date) is not int:
        raise TypeError("Injected FX date must be an integer")

    print("Controlled invalid FX types verified: 2")

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

    source_rates = inject_invalid_fx_types(all_rates)

    write_fx_rates(source_rates, REF_FX_RATES_OUTPUT_PATH)
    verify_fx_rates_file(source_rates, REF_FX_RATES_OUTPUT_PATH)
    verify_invalid_fx_types(REF_FX_RATES_OUTPUT_PATH)

    print(f"Written: {REF_FX_RATES_OUTPUT_PATH}")
    print(f"Valid API records fetched: {len(all_rates)}")
    print(f"Source records written: {len(source_rates)}")
    print("Intentionally invalid type records: 2")