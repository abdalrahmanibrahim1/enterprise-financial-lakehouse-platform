from datetime import datetime, timedelta
from faker import Faker
import random
from collections import Counter
from pprint import pprint

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

def generate_contacts(customers):
    contacts = []
    contact_counter = 1

    for customer in customers:
        customer_id = customer["customer_id"]
        customer_number = int(customer_id.replace("C", ""))

        mobile_contact = {
            "contact_id": f"CT{contact_counter:06d}",
            "customer_id": customer_id,
            "contact_type": "mobile",
            "contact_value": f"+96279{customer_number:07d}",
            "is_primary": True,
            "created_at": customer["created_at"],
            "updated_at": customer["updated_at"],
        }

        contacts.append(mobile_contact)
        contact_counter += 1

        if random.random() < 0.75:
            email_contact = {
                "contact_id": f"CT{contact_counter:06d}",
                "customer_id": customer_id,
                "contact_type": "email",
                "contact_value": f"{customer_id.lower()}@example.com",
                "is_primary": False,
                "created_at": customer["created_at"],
                "updated_at": customer["updated_at"],
            }

            contacts.append(email_contact)
            contact_counter += 1

        if random.random() < 0.25:
            phone_contact = {
                "contact_id": f"CT{contact_counter:06d}",
                "customer_id": customer_id,
                "contact_type": "phone",
                "contact_value": f"+9626{customer_number:07d}",
                "is_primary": False,
                "created_at": customer["created_at"],
                "updated_at": customer["updated_at"],
            }

            contacts.append(phone_contact)
            contact_counter += 1

    return contacts

def generate_customer_status_history(customers):
    statuses = []
    status_counter = 1

    for customer in customers:
        customer_id = customer["customer_id"]
        created_date = customer["created_at"].date()
        updated_date = customer["updated_at"].date()

        has_status_change = random.random() < 0.20 and updated_date > created_date

        if has_status_change:
            days_between = (updated_date - created_date).days
            change_date = created_date + timedelta(
                days=random.randint(1, days_between)
            )

            first_status = {
                "status_history_id": f"SH{status_counter:06d}",
                "customer_id": customer_id,
                "status": "Active",
                "valid_from": created_date,
                "valid_to": change_date,
                "updated_at": customer["updated_at"],
            }

            statuses.append(first_status)
            status_counter += 1

            second_status_value = random.choices(
                ["Dormant", "Suspended", "Closed"],
                weights=[70, 20, 10],
                k=1
            )[0]

            second_status = {
                "status_history_id": f"SH{status_counter:06d}",
                "customer_id": customer_id,
                "status": second_status_value,
                "valid_from": change_date,
                "valid_to": None,
                "updated_at": customer["updated_at"],
            }

            statuses.append(second_status)
            status_counter += 1

        else:
            status = {
                "status_history_id": f"SH{status_counter:06d}",
                "customer_id": customer_id,
                "status": "Active",
                "valid_from": created_date,
                "valid_to": None,
                "updated_at": customer["updated_at"],
            }

            statuses.append(status)
            status_counter += 1

    return statuses

def generate_crm_dataset(num_customers=100):
    segments = generate_segments()
    customers = generate_customers(num_customers)
    contacts = generate_contacts(customers)
    status_history = generate_customer_status_history(customers)

    return {
        "segments": segments,
        "customers": customers,
        "contacts": contacts,
        "status_history": status_history,
    }    

if __name__ == "__main__":
    crm_data = generate_crm_dataset(100)

    print(f"Segments: {len(crm_data['segments'])}")
    print(f"Customers: {len(crm_data['customers'])}")
    print(f"Contacts: {len(crm_data['contacts'])}")
    print(f"Status history: {len(crm_data['status_history'])}")