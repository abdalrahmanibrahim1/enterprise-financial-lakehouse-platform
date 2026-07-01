from datetime import datetime, timedelta
from faker import Faker
import random

random.seed(42)
Faker.seed(42)

def generate_segments():
    updated_at = datetime(2026, 1, 1, 0, 0, 0)

    segments = [
        {
            "segment_id": "SEG001",
            "segment_name": "Retail",
            "risk_band": "Low",
            "updated_at": updated_at,
        },
        {
            "segment_id": "SEG002",
            "segment_name": "Premium",
            "risk_band": "Medium",
            "updated_at": updated_at,
        },
        {
            "segment_id": "SEG003",
            "segment_name": "SME",
            "risk_band": "Medium",
            "updated_at": updated_at,
        },
        {
            "segment_id": "SEG004",
            "segment_name": "Corporate",
            "risk_band": "High",
            "updated_at": updated_at,
        },
        {
            "segment_id": "SEG005",
            "segment_name": "Private",
            "risk_band": "Low",
            "updated_at": updated_at,
        },
    ]

    return segments

def generate_customers(num_of_customers=100):
    fake = Faker()

    cities = [
        "Amman",
        "Irbid",
        "Zarqa",
        "Aqaba",
        "Salt",
        "Madaba",
        "Karak",
        "Mafraq",
        "Jerash",
        "Ajloun",
    ]

    city_weights = [
        44,  # Amman
        19,  # Irbid
        15,  # Zarqa
        2,   # Aqaba
        5,   # Salt / Balqa-ish
        2,   # Madaba
        3,   # Karak
        5,   # Mafraq
        3,   # Jerash
        2,   # Ajloun
    ]

    segment_ids = ["SEG001", "SEG002", "SEG003", "SEG004", "SEG005"]
    segment_weights = [55, 20, 12, 8, 5]

    customers = []

    min_birth_date = datetime(1950, 1, 1)
    max_birth_date = datetime(2005, 12, 31)

    min_create_date = datetime(2023, 1, 1)
    max_create_date = datetime(2025, 12, 31)
    max_update_date = datetime(2026, 6, 30)

    for i in range(1, num_of_customers + 1):
        gender = random.choice(["M", "F"])

        birth_date_range = (max_birth_date - min_birth_date).days
        birth_date = min_birth_date + timedelta(
            days=random.randint(0, birth_date_range)
        )

        create_date_range = (max_create_date - min_create_date).days
        created_at = min_create_date + timedelta(
            days=random.randint(0, create_date_range)
        )

        max_update_days = (max_update_date - created_at).days
        updated_at = created_at + timedelta(
            days=random.randint(0, max_update_days)
        )

        segment_id = random.choices(
            segment_ids,
            segment_weights,
            k=1
        )[0]

        city = random.choices(
            cities, 
            weights= city_weights,
            k = 1
        )[0]

        if gender == "F":
            full_name = fake.name_female()
        else:
            full_name = fake.name_male()

        customer = {
            "customer_id": f"C{i:06d}",
            "national_id": f"NAT{i:07d}",
            "full_name": full_name,
            "birth_date": birth_date.date(),
            "city": city,
            "gender": gender,
            "segment_id": segment_id,
            "created_at": created_at,
            "updated_at": updated_at,
        }

        customers.append(customer)

    return customers

if __name__ == "__main__":
    customers = generate_customers(5)

    for customer in customers:
        print(customer)