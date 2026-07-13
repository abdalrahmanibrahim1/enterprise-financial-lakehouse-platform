import random
from datetime import datetime, timedelta
from decimal import Decimal
import calendar
import math

MONEY_PRECISION = Decimal("0.001")


# Time-related constants
MAX_UPDATE_DATE = datetime(2026, 6, 30)
BANK_BUSINESS_START_HOUR = 8
BANK_BUSINESS_END_HOUR = 16
BANK_WEEKEND_DAYS = {4, 5}  # Friday=4, Saturday=5 in Python datetime.weekday()


#Product related constants
LOAN_LIKE_PRODUCTS = {"PRD005", "PRD006", "PRD008"}
CREDIT_CARD_PRODUCTS = {"PRD007"}
DEPOSIT_LIKE_PRODUCTS = {"PRD001", "PRD002", "PRD004"}
SALARY_LIKE_PRODUCTS = {"PRD003"}
PRODUCT_WEIGHTS_BY_SEGMENT = {
        # Retail: normal individual customers
        "SEG001": {
            "PRD001": 30,  # Current Account
            "PRD002": 30,  # Savings Account
            "PRD003": 25,  # Salary Account
            "PRD004": 1,   # Business Account - rare sole proprietor / micro-business edge case
            "PRD005": 6,   # Personal Loan
            "PRD006": 4,   # Auto Loan
            "PRD007": 3,   # Credit Card
            "PRD008": 1,   # Mortgage
        },

        # Premium: higher-value individual customers
        "SEG002": {
            "PRD001": 20,
            "PRD002": 30,
            "PRD003": 15,
            "PRD004": 3,
            "PRD005": 8,
            "PRD006": 5,
            "PRD007": 12,
            "PRD008": 7,
        },

        # SME: small/medium business customers
        "SEG003": {
            "PRD001": 25,
            "PRD002": 8,
            "PRD003": 0,
            "PRD004": 55,
            "PRD005": 0,
            "PRD006": 4,
            "PRD007": 6,
            "PRD008": 2,
        },

        # Corporate: large business/institution customers
        "SEG004": {
            "PRD001": 22,
            "PRD002": 3,
            "PRD003": 0,
            "PRD004": 63,
            "PRD005": 0,
            "PRD006": 2,
            "PRD007": 8,
            "PRD008": 2,
        },

        # Private: wealthy individual customers
        "SEG005": {
            "PRD001": 22,
            "PRD002": 35,
            "PRD003": 3,
            "PRD004": 5,
            "PRD005": 5,
            "PRD006": 5,
            "PRD007": 15,
            "PRD008": 10,
        },
    }

#Account related constants
ACCOUNT_COUNT_RULES = {
    "SEG001": {
        "options": [0, 1, 2, 3],
        "weights": [6, 70, 21, 3],
    },
    "SEG002": {
        "options": [0, 1, 2, 3],
        "weights": [2, 48, 35, 15],
    },
    "SEG003": {
        "options": [0, 1, 2, 3],
        "weights": [3, 37, 45, 15],
    },
    "SEG004": {
        "options": [0, 1, 2, 3],
        "weights": [1, 19, 45, 35],
    },
    "SEG005": {
        "options": [0, 1, 2, 3],
        "weights": [1, 34, 40, 25],
    },
}

BRANCH_WEIGHTS_BY_ID = {
    # Relative branch selection weights used when no same-city branch is selected.
    # Higher weights make central/high-volume branches more likely.
    "BR001": 25,
    "BR002": 20,
    "BR003": 15,
    "BR004": 12,
    "BR005": 5,
    "BR006": 5,
    "BR007": 4,
    "BR008": 4,
    "BR009": 5,
    "BR010": 5,
}

CURRENCY_RULES = {
        "SEG001": {"currencies": ["JOD", "USD", "EUR"], "weights": [90, 8, 2]},
        "SEG002": {"currencies": ["JOD", "USD", "EUR"], "weights": [78, 15, 7]},
        "SEG003": {"currencies": ["JOD", "USD", "EUR"], "weights": [75, 20, 5]},
        "SEG004": {"currencies": ["JOD", "USD", "EUR"], "weights": [65, 25, 10]},
        "SEG005": {"currencies": ["JOD", "USD", "EUR"], "weights": [75, 15, 10]},
    }

BALANCE_LIMIT_RULES = {
    # Opening funding amount for deposit-like accounts.
    # This value is inserted as an "Opening Deposit" credit transaction
    # when account activity begins.
        "SEG001": {
            "PRD001": [0, 7_500],
            "PRD002": [0, 20_000],
            "PRD004": [0, 25_000],
        },
        "SEG002": {
            "PRD001": [500, 25_000],
            "PRD002": [5_000, 100_000],
            "PRD004": [5_000, 75_000],
        },
        "SEG003": {
            "PRD001": [1_000, 75_000],
            "PRD002": [0, 50_000],
            "PRD004": [5_000, 250_000],
        },
        "SEG004": {
            "PRD001": [10_000, 500_000],
            "PRD002": [0, 250_000],
            "PRD004": [50_000, 2_000_000],
        },
        "SEG005": {
            "PRD001": [10_000, 150_000],
            "PRD002": [25_000, 750_000],
            "PRD004": [10_000, 250_000],
        },
    }


# Shared transaction metadata constants
MERCHANT_CATEGORIES_BY_TRANSACTION_TYPE = {
    # Merchant categories are only assigned to transaction types where the
    # counterparty/category is meaningful for analytics. Transfers, deposits,
    # repayments, fees, and system-generated transactions intentionally use None.
    "POS Purchase": [
        "Groceries",
        "Restaurants",
        "Fuel",
        "Retail",
        "Healthcare",
        "Education",
        "Entertainment",
        "Transportation",
        "Clothing",
        "Electronics",
    ],

    "Card Purchase": [
        "Groceries",
        "Restaurants",
        "Fuel",
        "Retail",
        "Travel",
        "Telecom",
        "Healthcare",
        "Education",
        "Entertainment",
        "Hotels",
        "Subscriptions",
        "Online Services",
        "Clothing",
        "Electronics",
    ],

    "Bill Payment": [
        "Utilities",
        "Telecom",
        "Government",
        "Insurance",
        "Education",
        "Healthcare",
    ],

    "Supplier Payment": [
        "Business Services",
        "Office Supplies",
        "Fuel",
        "Transportation",
        "Electronics",
    ],
}

CHANNEL_RULES_BY_TRANSACTION_TYPE = {
    # Relative channel weights by transaction type.
    # Only transaction types generated by the current product-specific transaction
    # generators are included here.

    "Opening Deposit": [
        {"channel": "Branch", "weight": 55},
        {"channel": "Online", "weight": 30},
        {"channel": "Mobile", "weight": 15},
    ],

    "Cash Deposit": [
        {"channel": "Branch", "weight": 70},
        {"channel": "ATM", "weight": 30},
    ],

    "ATM Withdrawal": [
        {"channel": "ATM", "weight": 100},
    ],

    "Transfer In": [
        {"channel": "Mobile", "weight": 40},
        {"channel": "Online", "weight": 40},
        {"channel": "Branch", "weight": 20},
    ],

    "Transfer Out": [
        {"channel": "Mobile", "weight": 45},
        {"channel": "Online", "weight": 40},
        {"channel": "Branch", "weight": 15},
    ],

    "Bill Payment": [
        {"channel": "Mobile", "weight": 55},
        {"channel": "Online", "weight": 35},
        {"channel": "Branch", "weight": 10},
    ],

    "POS Purchase": [
        {"channel": "POS", "weight": 85},
        {"channel": "Online", "weight": 15},
    ],

    "Customer Payment": [
        {"channel": "Online", "weight": 55},
        {"channel": "Mobile", "weight": 30},
        {"channel": "Branch", "weight": 15},
    ],

    "Supplier Payment": [
        {"channel": "Online", "weight": 55},
        {"channel": "Mobile", "weight": 25},
        {"channel": "Branch", "weight": 20},
    ],

    "Fee": [
        {"channel": "System", "weight": 100},
    ],

    "Interest Credit": [
        {"channel": "System", "weight": 100},
    ],

    "Interest Charge": [
        {"channel": "System", "weight": 100},
    ],

    "Salary Credit": [
        {"channel": "System", "weight": 100},
    ],

    "Account Closure Transfer": [
        {"channel": "System", "weight": 100},
    ],

    "Loan Disbursement": [
        {"channel": "System", "weight": 70},
        {"channel": "Branch", "weight": 30},
    ],

    "Loan Repayment": [
        {"channel": "Mobile", "weight": 35},
        {"channel": "Online", "weight": 35},
        {"channel": "Branch", "weight": 20},
        {"channel": "System", "weight": 10},
    ],

    "Card Purchase": [
        {"channel": "POS", "weight": 70},
        {"channel": "Online", "weight": 30},
    ],

    "Card Payment": [
        {"channel": "Mobile", "weight": 40},
        {"channel": "Online", "weight": 40},
        {"channel": "Branch", "weight": 15},
        {"channel": "ATM", "weight": 5},
    ],

    "Cash Advance": [
        {"channel": "ATM", "weight": 80},
        {"channel": "Branch", "weight": 20},
    ],

    "Cash Advance Fee": [
        {"channel": "System", "weight": 100},
    ],

    "Late Fee": [
        {"channel": "System", "weight": 100},
    ],
}


# Deposit transaction constants
DEPOSIT_TRANSACTION_TYPES = {
    # PRD001 - Current Account
     "PRD001": [
        {"transaction_type": "POS Purchase", "direction": "Debit", "weight": 30},
        {"transaction_type": "ATM Withdrawal", "direction": "Debit", "weight": 20},
        {"transaction_type": "Bill Payment", "direction": "Debit", "weight": 15},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 15},
        {"transaction_type": "Transfer In", "direction": "Credit", "weight": 15},
        {"transaction_type": "Cash Deposit", "direction": "Credit", "weight": 5},
    ],

    # PRD002 - Savings Account
    "PRD002": [
        {"transaction_type": "Transfer In", "direction": "Credit", "weight": 35},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 30},
        {"transaction_type": "Cash Deposit", "direction": "Credit", "weight": 15},
        {"transaction_type": "ATM Withdrawal", "direction": "Debit", "weight": 10},
        {"transaction_type": "Interest Credit", "direction": "Credit", "weight": 5},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 5},
    ],
    # PRD004 - Business Account
    "PRD004": [
        {"transaction_type": "Customer Payment", "direction": "Credit", "weight": 30},
        {"transaction_type": "Supplier Payment", "direction": "Debit", "weight": 25},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 15},
        {"transaction_type": "Transfer In", "direction": "Credit", "weight": 15},
        {"transaction_type": "Cash Deposit", "direction": "Credit", "weight": 10},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 5},
    ]
}

DEPOSIT_MONTHLY_TRANSACTION_COUNT_RULES = {
    "Active": {
        "PRD001": (3, 8),
        "PRD002": (1, 3),
        "PRD004": (5, 12),
    },
    "Dormant": {
        "PRD001": (0, 1),
        "PRD002": (0, 1),
        "PRD004": (0, 2),
    },
    "Blocked": {
        "PRD001": (0, 1),
        "PRD002": (0, 1),
        "PRD004": (0, 1),
    },
    "Closed": {
        "PRD001": (2, 6),
        "PRD002": (1, 2),
        "PRD004": (3, 10),
    },
}

SEGMENT_AMOUNT_MULTIPLIER = {
    "SEG001": Decimal("1.0"),
    "SEG002": Decimal("2.5"),
    "SEG003": Decimal("5.0"),
    "SEG004": Decimal("15.0"),
    "SEG005": Decimal("8.0"),
}

DEPOSIT_BASE_AMOUNT_RULES = {
    "POS Purchase": (5, 250),
    "ATM Withdrawal": (10, 500),
    "Bill Payment": (20, 700),
    "Transfer Out": (20, 1500),
    "Transfer In": (20, 2000),
    "Cash Deposit": (50, 3000),
    "Interest Credit": (1, 50),
    "Fee": (2, 30),
    "Customer Payment": (100, 5000),
    "Supplier Payment": (100, 6000),
}

DEPOSIT_ALLOWED_TRANSACTION_TYPES = {
    "PRD001": {
        "Opening Deposit",
        "POS Purchase",
        "ATM Withdrawal",
        "Bill Payment",
        "Transfer Out",
        "Transfer In",
        "Cash Deposit",
        "Account Closure Transfer",
    },
    "PRD002": {
        "Opening Deposit",
        "Transfer In",
        "Transfer Out",
        "Cash Deposit",
        "ATM Withdrawal",
        "Interest Credit",
        "Fee",
        "Account Closure Transfer",
    },
    "PRD004": {
        "Opening Deposit",
        "Customer Payment",
        "Supplier Payment",
        "Transfer Out",
        "Transfer In",
        "Cash Deposit",
        "Fee",
        "Account Closure Transfer",
    },
}

DEPOSIT_EXPECTED_DIRECTIONS = {
    "Opening Deposit": "Credit",

    "POS Purchase": "Debit",
    "ATM Withdrawal": "Debit",
    "Bill Payment": "Debit",
    "Transfer Out": "Debit",
    "Supplier Payment": "Debit",
    "Fee": "Debit",
    "Account Closure Transfer": "Debit",

    "Transfer In": "Credit",
    "Cash Deposit": "Credit",
    "Interest Credit": "Credit",
    "Customer Payment": "Credit",
}


#Loan transactions constants
LOAN_PRINCIPAL_AMOUNT_RULES = {
    "SEG001": {  # Retail
        "PRD005": [1_000, 25_000],      # Personal Loan
        "PRD006": [5_000, 45_000],      # Auto Loan
        "PRD008": [30_000, 120_000],    # Mortgage
    },
    "SEG002": {  # Premium
        "PRD005": [5_000, 60_000],
        "PRD006": [10_000, 70_000],
        "PRD008": [50_000, 250_000],
    },
    "SEG003": {  # SME
        "PRD006": [10_000, 100_000],    # Vehicle/business vehicle financing
        "PRD008": [50_000, 500_000],    # Business property financing
    },
    "SEG004": {  # Corporate
        "PRD006": [50_000, 500_000],    # Fleet financing
        "PRD008": [250_000, 5_000_000], # Commercial mortgage/property
    },
    "SEG005": {  # Private banking
        "PRD005": [10_000, 100_000],
        "PRD006": [30_000, 200_000],
        "PRD008": [100_000, 2_000_000],
    },
}

LOAN_TERM_MONTH_OPTIONS = {
    "PRD005": {
        "options": [12, 24, 36, 48, 60],
        "weights": [10, 25, 35, 20, 10],
    },
    "PRD006": {
        "options": [24, 36, 48, 60, 72, 84],
        "weights": [8, 18, 28, 25, 15, 6],
    },
    "PRD008": {
        "options": [120, 180, 240, 300],
        "weights": [10, 30, 40, 20],
    },
}

LOAN_LATE_PAYMENT_PROBABILITY_BY_SEGMENT = {
    "SEG001": 0.06,
    "SEG002": 0.03,
    "SEG003": 0.05,
    "SEG004": 0.02,
    "SEG005": 0.02,
}

LOAN_LATE_FEE_RULES = {
    "PRD005": [5, 35],
    "PRD006": [10, 50],
    "PRD008": [20, 150],
}


# Credit card transaction constants
CREDIT_CARD_LIMIT_RULES = {
    "SEG001": [500, 3_000],       # Retail
    "SEG002": [2_000, 10_000],    # Premium
    "SEG003": [3_000, 25_000],    # SME/business card
    "SEG004": [10_000, 100_000],  # Corporate card
    "SEG005": [5_000, 50_000],    # Private banking
}

CARD_CASH_ADVANCE_PROBABILITY_BY_SEGMENT = {
    "SEG001": 0.035,  # Retail
    "SEG002": 0.025,  # Premium
    "SEG003": 0.020,  # SME
    "SEG004": 0.010,  # Corporate
    "SEG005": 0.015,  # Private banking
}

CARD_CASH_ADVANCE_AMOUNT_RULES = {
    "SEG001": (20, 500),
    "SEG002": (50, 1_000),
    "SEG003": (100, 2_500),
    "SEG004": (500, 10_000),
    "SEG005": (200, 5_000),
}

CARD_CASH_ADVANCE_FEE_RULES = {
    "SEG001": {"rate": Decimal("0.040"), "min": Decimal("5.000")},
    "SEG002": {"rate": Decimal("0.035"), "min": Decimal("7.500")},
    "SEG003": {"rate": Decimal("0.030"), "min": Decimal("10.000")},
    "SEG004": {"rate": Decimal("0.025"), "min": Decimal("25.000")},
    "SEG005": {"rate": Decimal("0.030"), "min": Decimal("15.000")},
}

CARD_LATE_PAYMENT_PROBABILITY_BY_SEGMENT = {
    "SEG001": 0.05,  # Retail
    "SEG002": 0.03,  # Premium
    "SEG003": 0.04,  # SME
    "SEG004": 0.02,  # Corporate
    "SEG005": 0.02,  # Private banking
}

CARD_LATE_FEE_RULES = {
    "SEG001": [5, 25],
    "SEG002": [10, 35],
    "SEG003": [10, 50],
    "SEG004": [25, 150],
    "SEG005": [15, 75],
}

CARD_INTEREST_RATE_RULES = {
    "SEG001": Decimal("0.024"),  # Retail: 2.4% monthly
    "SEG002": Decimal("0.020"),  # Premium: 2.0% monthly
    "SEG003": Decimal("0.022"),  # SME: 2.2% monthly
    "SEG004": Decimal("0.018"),  # Corporate: 1.8% monthly
    "SEG005": Decimal("0.016"),  # Private banking: 1.6% monthly
}

CARD_MINIMUM_PAYMENT_RULES = {
    "SEG001": {"rate": Decimal("0.030"), "min": Decimal("10.000")},
    "SEG002": {"rate": Decimal("0.030"), "min": Decimal("15.000")},
    "SEG003": {"rate": Decimal("0.035"), "min": Decimal("20.000")},
    "SEG004": {"rate": Decimal("0.025"), "min": Decimal("50.000")},
    "SEG005": {"rate": Decimal("0.025"), "min": Decimal("25.000")},
}

CARD_PAYMENT_BEHAVIOR_RULES = {
    "SEG001": {
        "options": ["full", "partial", "minimum", "underpay"],
        "weights": [35, 40, 18, 7],
    },
    "SEG002": {
        "options": ["full", "partial", "minimum", "underpay"],
        "weights": [45, 38, 13, 4],
    },
    "SEG003": {
        "options": ["full", "partial", "minimum", "underpay"],
        "weights": [35, 42, 17, 6],
    },
    "SEG004": {
        "options": ["full", "partial", "minimum", "underpay"],
        "weights": [55, 35, 8, 2],
    },
    "SEG005": {
        "options": ["full", "partial", "minimum", "underpay"],
        "weights": [60, 32, 6, 2],
    },
}


# Salary account transaction constants
SALARY_AMOUNT_RULES = {
    "SEG001": [400, 2_500],      # Retail
    "SEG002": [1_000, 7_000],    # Premium
    "SEG005": [5_000, 20_000],   # Private banking
}

SALARY_MONTHLY_SPEND_RATIO_RULES = {
    "SEG001": [Decimal("0.65"), Decimal("0.95")],
    "SEG002": [Decimal("0.50"), Decimal("0.90")],
    "SEG005": [Decimal("0.35"), Decimal("0.80")],
}

SALARY_SPENDING_TYPES = [
    {"transaction_type": "POS Purchase", "direction": "Debit", "weight": 35},
    {"transaction_type": "ATM Withdrawal", "direction": "Debit", "weight": 25},
    {"transaction_type": "Bill Payment", "direction": "Debit", "weight": 20},
    {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 20},
]

SALARY_DAY_OPTIONS = [24, 25, 26, 27, 28, 30]

SALARY_MONTHLY_TRANSACTION_COUNT_RULES = {
    "SEG001": (12, 35),
    "SEG002": (18, 50),
    "SEG005": (20, 70),
}

# ============================================================
# Reference data generators
# ============================================================


def generate_branches():
    """Generate static branch reference data."""

    updated_at = datetime(2026, 1, 1, 0, 0, 0)

    branches = [
        {
            "branch_id": "BR001",
            "branch_name": "Amman Main Branch",
            "city": "Amman",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR002",
            "branch_name": "West Amman Branch",
            "city": "Amman",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR003",
            "branch_name": "Irbid Branch",
            "city": "Irbid",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR004",
            "branch_name": "Zarqa Branch",
            "city": "Zarqa",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR005",
            "branch_name": "Aqaba Branch",
            "city": "Aqaba",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR006",
            "branch_name": "Salt Branch",
            "city": "Salt",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR007",
            "branch_name": "Madaba Branch",
            "city": "Madaba",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR008",
            "branch_name": "Karak Branch",
            "city": "Karak",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR009",
            "branch_name": "Mafraq Branch",
            "city": "Mafraq",
            "updated_at": updated_at,
        },
        {
            "branch_id": "BR010",
            "branch_name": "Jerash Branch",
            "city": "Jerash",
            "updated_at": updated_at,
        },
    ]

    return branches

def generate_products():
    """Generate static product reference data."""
    updated_at = datetime(2026, 1, 1, 0, 0, 0)

    products = [
        {
            "product_id": "PRD001",
            "product_name": "Current Account",
            "product_type": "Deposit",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD002",
            "product_name": "Savings Account",
            "product_type": "Deposit",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD003",
            "product_name": "Salary Account",
            "product_type": "Deposit",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD004",
            "product_name": "Business Account",
            "product_type": "Deposit",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD005",
            "product_name": "Personal Loan",
            "product_type": "Loan",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD006",
            "product_name": "Auto Loan",
            "product_type": "Loan",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD007",
            "product_name": "Credit Card",
            "product_type": "Card",
            "updated_at": updated_at,
        },
        {
            "product_id": "PRD008",
            "product_name": "Mortgage",
            "product_type": "Loan",
            "updated_at": updated_at,
        },
    ]
    
    return products


# ============================================================
# Shared datetime helpers
# ============================================================


def is_bank_working_day(dt):
    """Return True if the date is a bank working day."""
    return dt.weekday() not in BANK_WEEKEND_DAYS

def move_to_next_bank_working_day(dt):
    """Move datetime to the next bank working day at opening hour."""
    next_dt = dt

    while not is_bank_working_day(next_dt):
        next_dt = next_dt + timedelta(days=1)

    return next_dt.replace(
        hour=BANK_BUSINESS_START_HOUR,
        minute=0,
        second=0,
        microsecond=0
    )

def assign_bank_business_time(base_datetime, earliest_allowed=None, latest_allowed=None):
    """Assign a random timestamp during bank working hours.

    Used for bank-side operational events such as account creation, loan
    disbursement, branch processing, and account closure actions.

    Bank working days are Sunday-Thursday.
    Bank working hours are 08:00:00-16:59:59.
    """
    search_start = base_datetime

    if earliest_allowed is not None and search_start < earliest_allowed:
        search_start = earliest_allowed

    if latest_allowed is not None and search_start > latest_allowed:
        raise ValueError("No valid bank business time: start is after latest allowed time")

    current_datetime = search_start

    while True:
        if latest_allowed is not None and current_datetime > latest_allowed:
            raise ValueError("No valid bank business time within allowed range")

        if not is_bank_working_day(current_datetime):
            current_datetime = move_to_next_bank_working_day(current_datetime)
            continue

        business_day_start = current_datetime.replace(
            hour=BANK_BUSINESS_START_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )

        business_day_end = current_datetime.replace(
            hour=BANK_BUSINESS_END_HOUR,
            minute=59,
            second=59,
            microsecond=0
        )

        window_start = max(business_day_start, current_datetime)

        if earliest_allowed is not None:
            window_start = max(window_start, earliest_allowed)

        window_end = business_day_end

        if latest_allowed is not None:
            window_end = min(window_end, latest_allowed)

        total_seconds = int((window_end - window_start).total_seconds())

        if total_seconds >= 0:
            return window_start + timedelta(
                seconds=random.randint(0, total_seconds)
            )

        current_datetime = (
            current_datetime + timedelta(days=1)
        ).replace(
            hour=BANK_BUSINESS_START_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )

def generate_transaction_timestamp(account):
    """Generate a random transaction timestamp inside the account activity window."""
    min_datetime = account["_activity_start_date"]
    max_datetime = account["_activity_end_date"]

    total_seconds = int(
        (max_datetime - min_datetime).total_seconds()
    )

    if total_seconds < 0:
        raise ValueError(
            f"Invalid activity window for account {account['account_id']}: "
            f"start {min_datetime} is after end {max_datetime}"
        )

    if total_seconds == 0:
        return min_datetime

    return min_datetime + timedelta(
        seconds=random.randint(0, total_seconds)
    )

def generate_created_at(transaction_timestamp):
    return transaction_timestamp + timedelta(
        minutes=random.randint(0, 10),
        seconds=random.randint(0, 59),
    )

def assign_random_business_time(base_datetime, earliest_allowed=None, latest_allowed=None):
    candidate = base_datetime.replace(
        hour=random.randint(8, 16),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )

    if earliest_allowed is not None and candidate < earliest_allowed:
        candidate = earliest_allowed

    if latest_allowed is not None and candidate > latest_allowed:
        candidate = latest_allowed

    return candidate

def get_account_created_at(account):
    if "created_at" in account:
        return account["created_at"]

    if "account_created_at" in account:
        return account["account_created_at"]

    raise KeyError(
        "Account is missing created_at/account_created_at. "
        "Opening Deposit audit needs the account creation timestamp."
    )

def get_valid_month_day(year, month, preferred_day):
    last_day_of_month = calendar.monthrange(year, month)[1]
    return min(preferred_day, last_day_of_month)

def add_one_month(dt):
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1)

    return dt.replace(month=dt.month + 1)


# ============================================================
# Shared transaction metadata helpers
# ===========================================================


def choose_merchant_category(transaction_type):
    categories = MERCHANT_CATEGORIES_BY_TRANSACTION_TYPE.get(transaction_type)

    if categories is None:
        return None

    return random.choice(categories)

def choose_channel(transaction_type):
    channel_rules = CHANNEL_RULES_BY_TRANSACTION_TYPE.get(transaction_type)

    if channel_rules is None:
        raise ValueError(
            f"No channel rules defined for transaction type: {transaction_type}"
        )

    channels = [
        channel_rule["channel"]
        for channel_rule in channel_rules
    ]

    weights = [
        channel_rule["weight"]
        for channel_rule in channel_rules
    ]

    return random.choices(
        channels,
        weights=weights,
        k=1
    )[0]


# ============================================================
# Account generation helpers
# ============================================================


def choose_account_count(segment_id):
    """Choose a segment-weighted number of accounts for a customer.

    A customer may receive zero accounts.
    """
    rule = ACCOUNT_COUNT_RULES[segment_id]

    return random.choices(
        rule["options"],
        weights = rule["weights"],
        k = 1
    )[0]

def choose_product_id(segment_id, available_product_ids):
    """Choose one eligible product for a customer using segment-based weights.

    The caller removes the chosen product from available_product_ids, so a
    customer cannot receive the same product more than once.
    """
    weights = [
        PRODUCT_WEIGHTS_BY_SEGMENT[segment_id][product_id]
        for product_id in available_product_ids
    ]

    return random.choices(
        available_product_ids,
        weights=weights,
        k=1
    )[0]

def choose_branch_id(customer_city, branches):
    """Choose a branch for an account.

    Customers usually use a branch in their own city when available.
    Otherwise, selection falls back to weighted random branch assignment.
    """
    same_city_branches = [
        branch for branch in branches
        if branch["city"] == customer_city
    ]

    if same_city_branches and random.random() < 0.85:
        return random.choice(same_city_branches)["branch_id"]
    
    branch_ids = [branch["branch_id"] for branch in branches]

    branch_weights = [
        BRANCH_WEIGHTS_BY_ID[branch_id]
        for branch_id in branch_ids
    ]

    return random.choices(
        branch_ids,
        weights=branch_weights,
        k=1
    )[0]

def choose_currency(segment_id):
    """Choose a segment-weighted account currency."""
    rule = CURRENCY_RULES[segment_id]

    return random.choices(
        rule["currencies"],
        weights=rule["weights"],
        k=1
    )[0]

def generate_opening_balance(segment_id, product_id):
    """Generate the initial funding amount for deposit-like accounts.

    For deposit-like accounts, this amount becomes the first ledger transaction
    when account activity begins. Loans, credit cards, and salary accounts start
    from zero because their balances are built from specialized schedules.
    """
    if (
        product_id in LOAN_LIKE_PRODUCTS
        or product_id in CREDIT_CARD_PRODUCTS
        or product_id in SALARY_LIKE_PRODUCTS
    ):
        return Decimal("0.000")
    
    min_balance, max_balance = BALANCE_LIMIT_RULES[segment_id][product_id]

    amount_in_thousandths = random.randint(
        min_balance * 1000,
        max_balance * 1000
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        MONEY_PRECISION
    )

def generate_activity_end_date(account_created_at, account_status):
    """Generate the final activity timestamp for an account.

    Active accounts remain open until MAX_UPDATE_DATE.
    Closed, blocked, and dormant accounts stop activity at a random point between account creation
    and MAX_UPDATE_DATE.
    """
    max_datetime = MAX_UPDATE_DATE.replace(
        hour=23,
        minute=59,
        second=59
    )

    if account_status == "Active":
        return max_datetime

    total_seconds = int((max_datetime - account_created_at).total_seconds())

    if total_seconds <= 0:
        raise ValueError("Account created_at is after MAX_UPDATE_DATE")

    return account_created_at + timedelta(
        seconds=random.randint(0, total_seconds)
    )

def generate_activity_start_date(account_created_at, activity_end_date):
    """Generate the first possible activity timestamp for an account.

    Activity starts within seven days of account creation, unless the account's
    activity window ends earlier.
    """
    latest_start_timestamp = min(
        account_created_at + timedelta(days=7),
        activity_end_date
    )

    total_seconds = int(
        (latest_start_timestamp - account_created_at).total_seconds()
    )

    if total_seconds < 0:
        raise ValueError("Activity end date is before account creation date")

    if total_seconds == 0:
        return account_created_at

    return account_created_at + timedelta(
        seconds=random.randint(0, total_seconds)
    )


# ============================================================
# Account generator
# ============================================================


def generate_accounts(customers, branches, products):
    """Generate account records for each customer.

    Account creation happens during bank business time.
    Product selection is done without replacement, so a customer cannot receive
    the same product more than once. 
    """
    accounts = []
    account_counter = 1

    max_datetime = MAX_UPDATE_DATE.replace(
        hour=23,
        minute=59,
        second=59
    )

    for customer in customers:
        customer_id = customer["customer_id"]
        customer_city = customer["city"]
        segment_id = customer["segment_id"]
        customer_created_at = customer["created_at"]

        if customer_created_at > max_datetime:
            raise ValueError("Customer created_at is after MAX_UPDATE_DATE")

        number_of_accounts = choose_account_count(segment_id)

        available_product_ids = [
            product["product_id"]
            for product in products
        ]

        days_after_customer_creation = (
            max_datetime - customer_created_at
        ).days

        for _ in range(number_of_accounts):
            product_id = choose_product_id(
                segment_id,
                available_product_ids
            )

            # Prevent duplicate products for the same customer.
            available_product_ids.remove(product_id)

            branch_id = choose_branch_id(
                customer_city,
                branches
            )

            account_created_at = assign_bank_business_time(
                customer_created_at + timedelta(
                    days=random.randint(0, days_after_customer_creation)
                ),
                earliest_allowed=customer_created_at,
                latest_allowed=max_datetime
            )
                
            account_status = random.choices(
                ["Active", "Dormant", "Closed", "Blocked"],
                weights=[85, 8, 5, 2],
                k=1
            )[0]

            activity_end_date = generate_activity_end_date(
                account_created_at,
                account_status
            )

            activity_start_date = generate_activity_start_date(
                account_created_at,
                activity_end_date
            )

            opening_balance = generate_opening_balance(
                segment_id,
                product_id
            )

            account = {
                "account_id": f"ACC{account_counter:06d}",
                "customer_id": customer_id,
                "branch_id": branch_id,
                "product_id": product_id,
                "account_open_date": account_created_at.date(),
                "account_status": account_status,
                "currency": choose_currency(segment_id),

                # Temporary value. Final current_balance is recalculated after
                # product-specific transactions are generated.
                "current_balance": opening_balance,

                # Internal generation fields, not inserted into the final source table.
                "_opening_balance": opening_balance,
                "_activity_start_date": activity_start_date,
                "_activity_end_date": activity_end_date,

                "created_at": account_created_at,

                # Temporary value. Final updated_at is set after transaction generation.
                "updated_at": activity_end_date,
            }

            accounts.append(account)
            account_counter += 1

    return accounts


# ============================================================
# Deposit transaction helpers
# ============================================================


def generate_deposit_transaction_amount(transaction_type, segment_id):
    """Generate a segment-adjusted amount for a deposit-like transaction."""
    min_amount, max_amount = DEPOSIT_BASE_AMOUNT_RULES[transaction_type]
    segment_multiplier = SEGMENT_AMOUNT_MULTIPLIER[segment_id]

    base_amount = Decimal(str(
        random.uniform(float(min_amount), float(max_amount))
    ))

    return (
        base_amount * segment_multiplier
    ).quantize(MONEY_PRECISION)

def estimate_active_months(start_date, end_date):
    """Estimate how many 30-day activity periods exist between two timestamps.

    Used to scale transaction counts based on how long the account was active.
    """
    active_seconds = (end_date - start_date).total_seconds()

    if active_seconds < 0:
        raise ValueError("End date is before start date")
    if active_seconds == 0:
        return 0

    seconds_per_month = 30 * 24 * 60 * 60

    return max(
        1,
        math.ceil(active_seconds / seconds_per_month)
    )

def split_deposit_lifecycle_months(account_status, total_months):
    """Split account lifetime into normal active months and final-state months.

    account_status is the final/current status, not necessarily the behavior
    across the whole account lifetime.
    """
    if total_months <= 0:
        return 0, 0

    if account_status == "Active":
        return total_months, 0

    if account_status == "Closed":
        final_state_months = 1
        active_months = max(0, total_months - final_state_months)
        return active_months, final_state_months

    if account_status == "Dormant":
        final_state_months = min(3, total_months)
        active_months = max(0, total_months - final_state_months)
        return active_months, final_state_months

    if account_status == "Blocked":
        final_state_months = 1
        active_months = max(0, total_months - final_state_months)
        return active_months, final_state_months

    raise ValueError(f"Unknown account status: {account_status}")

def generate_random_timestamps(start_datetime, end_datetime, count):
    """Generate sorted random timestamps inside a time window."""
    if count <= 0:
        return []

    total_seconds = int(
        (end_datetime - start_datetime).total_seconds()
    )

    if total_seconds < 0:
        return []

    if total_seconds == 0:
        return [start_datetime for _ in range(count)]

    return sorted([
        start_datetime + timedelta(
            seconds=random.randint(0, total_seconds)
        )
        for _ in range(count)
    ])

# ============================================================
# Deposit transaction generator
# ============================================================


def generate_deposit_like_transactions(account, segment_id, starting_transaction_counter):
    """Generate ledger transactions for deposit-like accounts.

    Deposit-like accounts start with optional opening funding, then receive
    normal customer activity across their active-life phase and lower-volume
    final-state activity before becoming dormant, blocked, or closed.
    """

    deposit_transactions = []

    product_id = account["product_id"]
    account_status = account["account_status"]

    if product_id not in DEPOSIT_LIKE_PRODUCTS:
        raise ValueError(
            f"Invalid deposit-like product passed: {product_id}"
        )

    running_balance = Decimal("0.000")
    opening_balance = account["_opening_balance"].quantize(MONEY_PRECISION)

    schedule_start = account["_activity_start_date"]
    schedule_end = account["_activity_end_date"]

    # If the account was opened with initial funding, insert it as the first
    # ledger transaction at the beginning of the activity window.
    if opening_balance > 0:
        opening_deposit_timestamp = account["_activity_start_date"]

        opening_deposit_transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": opening_deposit_timestamp,
            "transaction_type": "Opening Deposit",
            "transaction_direction": "Credit",
            "amount": opening_balance,
            "currency": account["currency"],
            "channel": choose_channel("Opening Deposit"),
            "merchant_category": None,
            "created_at": generate_created_at(opening_deposit_timestamp),
        }

        deposit_transactions.append(opening_deposit_transaction)
        starting_transaction_counter += 1

    running_balance = opening_balance

    total_months = estimate_active_months(
        schedule_start,
        schedule_end
    )

    # account_status is the final/current state, not the behavior of the
    # account's entire lifetime. Split the lifetime into active months and
    # final-state months so dormant/closed/blocked accounts still have normal
    # activity before reaching their final state.
    active_months, final_state_months = split_deposit_lifecycle_months(
        account_status,
        total_months
    )

    # Closed accounts reserve schedule_end for the closure transfer, so random
    # customer transactions must happen before the final closure timestamp.
    normal_activity_end = schedule_end

    if account_status == "Closed":
        normal_activity_end = schedule_end - timedelta(seconds=1)

    # Model the final-state phase as the last N months before activity ends.
    # Example: a dormant account with 10 total months may have 7 active months
    # followed by 3 low-activity dormant months.
    if final_state_months > 0:
        final_state_start = normal_activity_end - timedelta(
            days=30 * final_state_months
        )

        final_state_start = max(
            final_state_start,
            schedule_start
        )

        active_phase_end = final_state_start - timedelta(seconds=1)
    else:
        final_state_start = None
        active_phase_end = normal_activity_end

    active_min, active_max = DEPOSIT_MONTHLY_TRANSACTION_COUNT_RULES[
        "Active"
    ][product_id]

    if active_months > 0:
        active_transaction_count = random.randint(
            active_min * active_months,
            active_max * active_months
        )
    else:
        active_transaction_count = 0

    # Generate active-life transactions in the earlier phase using Active rules.
    active_timestamps = generate_random_timestamps(
        schedule_start,
        active_phase_end,
        active_transaction_count
    )

    # Generate final-state transactions near the end using the account's final
    # status rules, such as Dormant, Blocked, or Closed.
    if final_state_months > 0:
        final_min, final_max = DEPOSIT_MONTHLY_TRANSACTION_COUNT_RULES[
            account_status
        ][product_id]

        final_transaction_count = random.randint(
            final_min * final_state_months,
            final_max * final_state_months
        )

        final_timestamps = generate_random_timestamps(
            final_state_start,
            normal_activity_end,
            final_transaction_count
        )
    else:
        final_timestamps = []

    transaction_timestamps = sorted(
        active_timestamps + final_timestamps
    )

    # Generate transactions in chronological order while updating the running
    # balance after each transaction.
    for transaction_timestamp in transaction_timestamps:
        possible_transaction_types = DEPOSIT_TRANSACTION_TYPES[product_id]

        transaction_type_weights = [
            transaction_type["weight"]
            for transaction_type in possible_transaction_types
        ]

        chosen_transaction = random.choices(
            possible_transaction_types,
            weights=transaction_type_weights,
            k=1
        )[0]

        transaction_type = chosen_transaction["transaction_type"]
        transaction_direction = chosen_transaction["direction"]

        transaction_amount = generate_deposit_transaction_amount(
            transaction_type,
            segment_id
        )

        # Deposit-like accounts cannot go negative. Cap debit amounts to the
        # available balance and skip zero-value debits.
        if transaction_direction == "Debit":
            transaction_amount = min(
                transaction_amount,
                running_balance
            ).quantize(MONEY_PRECISION)

            if transaction_amount <= 0:
                continue

            running_balance = (
                running_balance - transaction_amount
            ).quantize(MONEY_PRECISION)

        else:
            running_balance = (
                running_balance + transaction_amount
            ).quantize(MONEY_PRECISION)

        transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": transaction_timestamp,
            "transaction_type": transaction_type,
            "transaction_direction": transaction_direction,
            "amount": transaction_amount,
            "currency": account["currency"],
            "channel": choose_channel(transaction_type),
            "merchant_category": choose_merchant_category(transaction_type),
            "created_at": generate_created_at(transaction_timestamp),
        }

        deposit_transactions.append(transaction)
        starting_transaction_counter += 1

    # Closed accounts must end at zero. Transfer out any remaining balance at
    # the exact activity end timestamp.
    if account_status == "Closed" and running_balance > 0:
        closure_amount = running_balance.quantize(MONEY_PRECISION)

        closure_transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": schedule_end,
            "transaction_type": "Account Closure Transfer",
            "transaction_direction": "Debit",
            "amount": closure_amount,
            "currency": account["currency"],
            "channel": choose_channel("Account Closure Transfer"),
            "merchant_category": None,
            "created_at": generate_created_at(schedule_end),
        }

        deposit_transactions.append(closure_transaction)
        starting_transaction_counter += 1

        running_balance = Decimal("0.000")

    # Store the generated ending balance back on the account record.
    account["current_balance"] = running_balance.quantize(MONEY_PRECISION)

    return deposit_transactions, starting_transaction_counter


# ============================================================
# Loan transaction helpers
# ============================================================


def generate_loan_principal_amount(segment_id, product_id):
    segment_rules = LOAN_PRINCIPAL_AMOUNT_RULES.get(segment_id)

    if segment_rules is None:
        raise ValueError(f"No loan principal rules for segment {segment_id}")

    limits = segment_rules.get(product_id)

    if not limits:
        raise ValueError(
            f"No loan principal rule for segment {segment_id}, "
            f"product {product_id}"
        )

    min_amount, max_amount = limits

    amount_in_thousandths = random.randint(
        min_amount * 1000,
        max_amount * 1000
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def choose_loan_term_months(product_id):
    rule = LOAN_TERM_MONTH_OPTIONS[product_id]

    return random.choices(
        rule["options"],
        weights=rule["weights"],
        k=1
    )[0]


# ============================================================
# Loan transaction generator
# ============================================================


def generate_loan_like_transactions(account, segment_id, starting_transaction_counter):
    """Generate loan disbursement, repayment, and late-fee transactions.

    Loan accounts start with one disbursement, followed by scheduled monthly
    repayments until either the loan term finishes or the account activity
    window ends.

    If the loan term finishes before activity_end_date, the final scheduled
    payment clears the remaining outstanding balance. Closed accounts are force
    settled at activity_end_date. Dormant and blocked loans are not force
    settled, so they may keep an outstanding balance.
    """

    loan_transactions = []

    schedule_end_date = account["_activity_end_date"]

    # 1. Generate original loan amount
    disbursement_amount = generate_loan_principal_amount(
        segment_id,
        account["product_id"],
    ).quantize(Decimal("0.001"))

    outstanding_balance = disbursement_amount

    # 2. Disbursement happens near account opening
    disbursement_date = account["_activity_start_date"]

    disbursement_timestamp = assign_random_business_time(
        disbursement_date,
        earliest_allowed=account["_activity_start_date"],
        latest_allowed=schedule_end_date)

    transaction = {
        "transaction_id": f"TR{starting_transaction_counter:06d}",
        "account_id": account["account_id"],
        "transaction_timestamp": disbursement_timestamp,
        "transaction_type": "Loan Disbursement",
        "transaction_direction": "Debit",
        "amount": disbursement_amount,
        "currency": account["currency"],
        "channel": choose_channel("Loan Disbursement"),
        "merchant_category": None,
        "created_at": generate_created_at(disbursement_timestamp),
    }

    loan_transactions.append(transaction)
    starting_transaction_counter += 1

    # 3. Choose loan term and monthly repayment
    loan_term_months = choose_loan_term_months(account["product_id"])

    monthly_repayment_amount = (
        disbursement_amount / Decimal(loan_term_months)
    ).quantize(Decimal("0.001"))

    payment_day = disbursement_timestamp.day

    payment_cycle = disbursement_timestamp.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    # 4. Generate monthly repayments, but never past schedule_end_date
    for i in range(1, loan_term_months + 1):
        payment_cycle = add_one_month(payment_cycle)

        valid_payment_day = get_valid_month_day(
            payment_cycle.year,
            payment_cycle.month,
            payment_day
        )

        payment_date = payment_cycle.replace(
            day=valid_payment_day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        if payment_date > schedule_end_date:
            break

        if outstanding_balance <= 0:
            break

        payment_timestamp = assign_random_business_time(
            payment_date,
            earliest_allowed=account["_activity_start_date"],
            latest_allowed=schedule_end_date)

        is_late_payment = (
            random.random() < LOAN_LATE_PAYMENT_PROBABILITY_BY_SEGMENT[segment_id]
        )

        if is_late_payment:
            late_days = random.randint(1, 7)
            late_payment_timestamp = payment_timestamp + timedelta(days=late_days)

            if late_payment_timestamp <= schedule_end_date:
                payment_timestamp = late_payment_timestamp

                fee_min, fee_max = LOAN_LATE_FEE_RULES[account["product_id"]]

                fee_amount = Decimal(
                    random.randint(fee_min * 1000, fee_max * 1000)
                ) / Decimal("1000")

                fee_amount = fee_amount.quantize(Decimal("0.001"))

                late_fee_transaction = {
                    "transaction_id": f"TR{starting_transaction_counter:06d}",
                    "account_id": account["account_id"],
                    "transaction_timestamp": payment_timestamp,
                    "transaction_type": "Late Fee",
                    "transaction_direction": "Debit",
                    "amount": fee_amount,
                    "currency": account["currency"],
                    "channel": choose_channel("Late Fee"),
                    "merchant_category": None,
                    "created_at": generate_created_at(payment_timestamp),
                }
            
                loan_transactions.append(late_fee_transaction)
                starting_transaction_counter += 1

                outstanding_balance = (
                    outstanding_balance + fee_amount
                ).quantize(MONEY_PRECISION)

        is_final_scheduled_payment = i == loan_term_months

        if is_final_scheduled_payment:
            repayment_amount = outstanding_balance.quantize(MONEY_PRECISION)
        else:
            repayment_amount = min(
                monthly_repayment_amount,
                outstanding_balance
            ).quantize(MONEY_PRECISION)


        transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": payment_timestamp,
            "transaction_type": "Loan Repayment",
            "transaction_direction": "Credit",
            "amount": repayment_amount,
            "currency": account["currency"],
            "channel": choose_channel("Loan Repayment"),
            "merchant_category": None,
            "created_at": generate_created_at(payment_timestamp),
        }

        loan_transactions.append(transaction)
        starting_transaction_counter += 1

        outstanding_balance = (
            outstanding_balance - repayment_amount
        ).quantize(Decimal("0.001"))

    # 5. If account is closed force final settlement
    if account["account_status"] == "Closed" and outstanding_balance > 0:
        settlement_timestamp = schedule_end_date

        transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": settlement_timestamp,
            "transaction_type": "Loan Repayment",
            "transaction_direction": "Credit",
            "amount": outstanding_balance.quantize(Decimal("0.001")),
            "currency": account["currency"],
            "channel": choose_channel("Loan Repayment"),
            "merchant_category": None,
            "created_at": generate_created_at(settlement_timestamp),
        }

        loan_transactions.append(transaction)
        starting_transaction_counter += 1

        outstanding_balance = Decimal("0.000")

    return loan_transactions, starting_transaction_counter


# ============================================================
# Credit card transaction helpers
# ============================================================


def choose_credit_card_limit(segment_id):
    """Choose a segment-based credit limit for a credit card account."""
    min_limit, max_limit = CREDIT_CARD_LIMIT_RULES[segment_id]

    amount_in_thousandths = random.randint(
        min_limit * 1000,
        max_limit * 1000
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def generate_card_purchase_amount(credit_limit):
    """Generate a card purchase amount capped as a percentage of credit limit."""
    max_purchase = credit_limit * Decimal("0.12")

    if max_purchase < Decimal("5.000"):
        max_purchase = Decimal("5.000")

    amount_in_thousandths = random.randint(
        2 * 1000,
        int(max_purchase * 1000)
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def generate_cash_advance_amount(credit_limit):
    """Generate a cash advance amount capped relative to the credit limit."""
    max_advance = max(Decimal("20.000"), credit_limit * Decimal("0.20"))

    amount_in_thousandths = random.randint(
        20 * 1000,
        int(max_advance * 1000)
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def calculate_minimum_card_payment(statement_balance, segment_id):
    """Calculate the minimum required payment for a card statement.

    The minimum payment is the larger of a fixed segment minimum and a
    percentage of the statement balance, but it never exceeds the full
    statement balance.
    """
    rule = CARD_MINIMUM_PAYMENT_RULES[segment_id]

    minimum_payment = max(
        rule["min"],
        statement_balance * rule["rate"]
    )

    return min(
        minimum_payment,
        statement_balance
    ).quantize(Decimal("0.001"))

def generate_card_late_fee_amount(segment_id):
    """Generate a segment-based late fee amount."""
    min_fee, max_fee = CARD_LATE_FEE_RULES[segment_id]
    fee = Decimal(random.randint(min_fee, max_fee)).quantize(Decimal("0.001"))

    return fee

def calculate_card_interest_charge(unpaid_statement_balance, segment_id):
    """Calculate monthly interest on the unpaid statement balance."""
    if unpaid_statement_balance <= 0:
        return Decimal("0.000")

    interest_rate = CARD_INTEREST_RATE_RULES[segment_id]

    interest = (
        unpaid_statement_balance * interest_rate
    ).quantize(Decimal("0.001"))

    return interest

def calculate_cash_advance_fee(cash_advance_amount, segment_id):
    """Calculate the fee charged for a cash advance transaction."""
    rule = CARD_CASH_ADVANCE_FEE_RULES[segment_id]

    fee = max(
        cash_advance_amount * rule["rate"],
        rule["min"]
    ).quantize(Decimal("0.001"))

    return fee


# ============================================================
# Credit card transaction generator
# ============================================================


def generate_credit_card_transactions(account, segment_id, starting_transaction_counter):
    """Generate credit card purchases, cash advances, payments, fees, and interest.

    Credit card accounts use an internal positive outstanding balance:
    purchases, cash advances, fees, and interest increase the outstanding
    balance, while card payments reduce it.

    This generator uses simplified monthly card cycles. Purchases happen before
    the payment point inside the same cycle, then the customer pays according to
    segment-level payment behavior. Closed card accounts are settled to zero at
    activity_end_date.
    """
    card_transactions = []

    schedule_start_date = account["_activity_start_date"]
    schedule_end_date = account["_activity_end_date"]

    credit_limit = choose_credit_card_limit(segment_id)
    account["_credit_limit"] = credit_limit

    outstanding_balance = Decimal("0.000")

    # Use calendar-month card cycles anchored to the account activity start day.
    cycle_day = schedule_start_date.day

    current_cycle_month = schedule_start_date.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    current_cycle_date = schedule_start_date

    while current_cycle_date <= schedule_end_date:
        cycle_start_date = current_cycle_date

        next_cycle_month = add_one_month(current_cycle_month)

        next_cycle_day = get_valid_month_day(
            next_cycle_month.year,
            next_cycle_month.month,
            cycle_day
        )

        next_cycle_start_date = next_cycle_month.replace(
            day=next_cycle_day,
            hour=schedule_start_date.hour,
            minute=schedule_start_date.minute,
            second=schedule_start_date.second,
            microsecond=0
        )

        cycle_end_date = min(
            next_cycle_start_date - timedelta(seconds=1),
            schedule_end_date
        )

        # Simplified payment model:
        # the customer pays near the end of the same card cycle instead of
        # carrying a separate statement balance into the next cycle.
        payment_date = min(
            cycle_start_date + timedelta(days=random.randint(20, 30)),
            cycle_end_date
        )

        payment_timestamp = assign_random_business_time(
            payment_date,
            earliest_allowed=cycle_start_date,
            latest_allowed=cycle_end_date
        )

        # In the final cycle of a closed card, skip the normal payment logic.
        # Purchases may happen until activity_end_date, then the card is settled.
        is_final_closed_cycle = (
            account["account_status"] == "Closed"
            and cycle_end_date == schedule_end_date
        )

        purchase_cutoff_timestamp = payment_timestamp

        if is_final_closed_cycle:
            purchase_cutoff_timestamp = schedule_end_date

        purchase_window_seconds = int(
            (purchase_cutoff_timestamp - cycle_start_date).total_seconds()
        )

        # Short partial cycles receive fewer purchases than full monthly cycles.
        cycle_days = max(
            1,
            (cycle_end_date - cycle_start_date).days + 1
        )

        if cycle_days < 7:
            purchase_count = random.randint(0, 3)
        elif cycle_days < 15:
            purchase_count = random.randint(1, 6)
        else:
            purchase_count = random.randint(3, 12)

        # Generate normal card purchases while respecting the credit limit.
        for _ in range(purchase_count):
            if purchase_window_seconds <= 0:
                break

            if outstanding_balance >= credit_limit:
                break

            available_credit = (
                credit_limit - outstanding_balance
            ).quantize(MONEY_PRECISION)

            if available_credit <= 0:
                break

            purchase_amount = generate_card_purchase_amount(credit_limit)

            purchase_amount = min(
                purchase_amount,
                available_credit
            ).quantize(MONEY_PRECISION)

            purchase_timestamp = cycle_start_date + timedelta(
                seconds=random.randint(0, purchase_window_seconds)
            )

            transaction = {
                "transaction_id": f"TR{starting_transaction_counter:06d}",
                "account_id": account["account_id"],
                "transaction_timestamp": purchase_timestamp,
                "transaction_type": "Card Purchase",
                "transaction_direction": "Debit",
                "amount": purchase_amount,
                "currency": account["currency"],
                "channel": choose_channel("Card Purchase"),
                "merchant_category": choose_merchant_category("Card Purchase"),
                "created_at": generate_created_at(purchase_timestamp),
            }

            card_transactions.append(transaction)
            starting_transaction_counter += 1

            outstanding_balance = (
                outstanding_balance + purchase_amount
            ).quantize(MONEY_PRECISION)

        available_credit = (
            credit_limit - outstanding_balance
        ).quantize(MONEY_PRECISION)

        # Cash advances are optional card activity. If generated, they increase
        # the outstanding balance and immediately create a cash advance fee when
        # enough credit remains.
        if (
            purchase_window_seconds > 0
            and available_credit > 0
            and random.random() < CARD_CASH_ADVANCE_PROBABILITY_BY_SEGMENT[segment_id]
        ):
            cash_advance_amount = generate_cash_advance_amount(credit_limit)

            cash_advance_amount = min(
                cash_advance_amount,
                available_credit
            ).quantize(MONEY_PRECISION)

            cash_advance_timestamp = cycle_start_date + timedelta(
                seconds=random.randint(0, purchase_window_seconds)
            )

            transaction = {
                "transaction_id": f"TR{starting_transaction_counter:06d}",
                "account_id": account["account_id"],
                "transaction_timestamp": cash_advance_timestamp,
                "transaction_type": "Cash Advance",
                "transaction_direction": "Debit",
                "amount": cash_advance_amount,
                "currency": account["currency"],
                "channel": choose_channel("Cash Advance"),
                "merchant_category": None,
                "created_at": generate_created_at(cash_advance_timestamp),
            }

            card_transactions.append(transaction)
            starting_transaction_counter += 1

            outstanding_balance = (
                outstanding_balance + cash_advance_amount
            ).quantize(MONEY_PRECISION)

            cash_advance_fee_amount = calculate_cash_advance_fee(
                cash_advance_amount,
                segment_id
            )

            available_credit = (
                credit_limit - outstanding_balance
            ).quantize(MONEY_PRECISION)

            cash_advance_fee_amount = min(
                cash_advance_fee_amount,
                available_credit
            ).quantize(MONEY_PRECISION)

            if cash_advance_fee_amount > 0:
                transaction = {
                    "transaction_id": f"TR{starting_transaction_counter:06d}",
                    "account_id": account["account_id"],
                    "transaction_timestamp": cash_advance_timestamp,
                    "transaction_type": "Cash Advance Fee",
                    "transaction_direction": "Debit",
                    "amount": cash_advance_fee_amount,
                    "currency": account["currency"],
                    "channel": choose_channel("Cash Advance Fee"),
                    "merchant_category": None,
                    "created_at": generate_created_at(cash_advance_timestamp),
                }

                card_transactions.append(transaction)
                starting_transaction_counter += 1

                outstanding_balance = (
                    outstanding_balance + cash_advance_fee_amount
                ).quantize(MONEY_PRECISION)

        # Calculate this cycle's statement balance and generate customer payment
        # behavior: full payment, minimum payment, partial payment, or underpayment.
        if outstanding_balance > 0 and not is_final_closed_cycle:
            statement_balance = outstanding_balance

            minimum_due = calculate_minimum_card_payment(
                statement_balance,
                segment_id
            )

            behavior_rule = CARD_PAYMENT_BEHAVIOR_RULES[segment_id]

            payment_behavior = random.choices(
                behavior_rule["options"],
                weights=behavior_rule["weights"],
                k=1
            )[0]

            if payment_behavior == "full":
                payment_amount = statement_balance

            elif payment_behavior == "minimum":
                payment_amount = minimum_due

            elif payment_behavior == "partial":
                if minimum_due >= statement_balance:
                    payment_amount = statement_balance
                else:
                    payment_ratio = Decimal(str(random.uniform(0.25, 0.95)))
                    payment_amount = statement_balance * payment_ratio

                    if payment_amount < minimum_due:
                        payment_amount = minimum_due

            elif payment_behavior == "underpay":
                payment_ratio = Decimal(str(random.uniform(0.00, 0.90)))
                payment_amount = minimum_due * payment_ratio

            payment_amount = payment_amount.quantize(MONEY_PRECISION)

            is_payment_date_late = (
                random.random()
                < CARD_LATE_PAYMENT_PROBABILITY_BY_SEGMENT[segment_id]
            )

            missed_minimum_payment = (
                payment_amount < minimum_due
            )

            should_charge_late_fee = (
                is_payment_date_late
                or missed_minimum_payment
            )

            should_charge_interest = (
                payment_amount < statement_balance
            )

            due_timestamp = payment_timestamp

            if is_payment_date_late:
                actual_payment_timestamp = min(
                    due_timestamp + timedelta(days=random.randint(1, 7)),
                    cycle_end_date
                )
            else:
                actual_payment_timestamp = due_timestamp

            # Late fees are charged when the payment is late or when the
            # customer pays less than the required minimum.
            if should_charge_late_fee:
                late_fee_amount = generate_card_late_fee_amount(segment_id)

                available_credit = (
                    credit_limit - outstanding_balance
                ).quantize(MONEY_PRECISION)

                late_fee_amount = min(
                    late_fee_amount,
                    available_credit
                ).quantize(MONEY_PRECISION)

                if late_fee_amount > 0:
                    transaction = {
                        "transaction_id": f"TR{starting_transaction_counter:06d}",
                        "account_id": account["account_id"],
                        "transaction_timestamp": actual_payment_timestamp,
                        "transaction_type": "Late Fee",
                        "transaction_direction": "Debit",
                        "amount": late_fee_amount,
                        "currency": account["currency"],
                        "channel": choose_channel("Late Fee"),
                        "merchant_category": None,
                        "created_at": generate_created_at(actual_payment_timestamp),
                    }

                    card_transactions.append(transaction)
                    starting_transaction_counter += 1

                    outstanding_balance = (
                        outstanding_balance + late_fee_amount
                    ).quantize(MONEY_PRECISION)

            # Customer payment reduces the outstanding balance.
            if payment_amount > 0:
                transaction = {
                    "transaction_id": f"TR{starting_transaction_counter:06d}",
                    "account_id": account["account_id"],
                    "transaction_timestamp": actual_payment_timestamp,
                    "transaction_type": "Card Payment",
                    "transaction_direction": "Credit",
                    "amount": payment_amount,
                    "currency": account["currency"],
                    "channel": choose_channel("Card Payment"),
                    "merchant_category": None,
                    "created_at": generate_created_at(actual_payment_timestamp),
                }

                card_transactions.append(transaction)
                starting_transaction_counter += 1

                outstanding_balance = (
                    outstanding_balance - payment_amount
                ).quantize(MONEY_PRECISION)

            # Interest is charged when the customer does not pay the full
            # statement balance.
            if should_charge_interest:
                unpaid_statement_balance = (
                    statement_balance - payment_amount
                ).quantize(MONEY_PRECISION)

                interest_amount = calculate_card_interest_charge(
                    unpaid_statement_balance,
                    segment_id
                )

                available_credit = (
                    credit_limit - outstanding_balance
                ).quantize(MONEY_PRECISION)

                interest_amount = min(
                    interest_amount,
                    available_credit
                ).quantize(MONEY_PRECISION)

                if interest_amount > 0:
                    transaction = {
                        "transaction_id": f"TR{starting_transaction_counter:06d}",
                        "account_id": account["account_id"],
                        "transaction_timestamp": actual_payment_timestamp,
                        "transaction_type": "Interest Charge",
                        "transaction_direction": "Debit",
                        "amount": interest_amount,
                        "currency": account["currency"],
                        "channel": choose_channel("Interest Charge"),
                        "merchant_category": None,
                        "created_at": generate_created_at(actual_payment_timestamp),
                    }

                    card_transactions.append(transaction)
                    starting_transaction_counter += 1

                    outstanding_balance = (
                        outstanding_balance + interest_amount
                    ).quantize(MONEY_PRECISION)

        # Move to the next calendar-month card cycle.
        current_cycle_month = next_cycle_month
        current_cycle_date = next_cycle_start_date

    # Closed card accounts must end at zero. Any remaining outstanding balance
    # is settled as a final card payment at the activity end timestamp.
    if account["account_status"] == "Closed" and outstanding_balance > 0:
        settlement_timestamp = account["_activity_end_date"]

        transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": settlement_timestamp,
            "transaction_type": "Card Payment",
            "transaction_direction": "Credit",
            "amount": outstanding_balance.quantize(MONEY_PRECISION),
            "currency": account["currency"],
            "channel": choose_channel("Card Payment"),
            "merchant_category": None,
            "created_at": generate_created_at(settlement_timestamp),
        }

        card_transactions.append(transaction)
        starting_transaction_counter += 1

        outstanding_balance = Decimal("0.000")

    return card_transactions, starting_transaction_counter

# ============================================================
# Salary account transaction helpers
# ============================================================


def choose_monthly_salary(segment_id):
    min_salary, max_salary = SALARY_AMOUNT_RULES[segment_id]

    amount_in_thousandths = random.randint(
        min_salary * 1000,
        max_salary * 1000
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def generate_total_salary_spending_amount(monthly_salary, segment_id):
    min_ratio, max_ratio = SALARY_MONTHLY_SPEND_RATIO_RULES[segment_id]

    spending_ratio = Decimal(str(
        random.uniform(
            float(min_ratio),
            float(max_ratio)
        )
    ))

    spending_amount = (
        monthly_salary * spending_ratio
    ).quantize(Decimal("0.001"))

    return spending_amount


# ============================================================
# Salary account transaction generator
# ============================================================


def generate_salary_account_transactions(account, segment_id, starting_transaction_counter):
    """Generate salary credits and spending activity for salary accounts.

    Salary accounts receive one recurring monthly salary credit on a stable
    salary day. After each salary credit, the account generates spending
    transactions until the next salary cycle or until activity_end_date.

    Spending is scaled down for partial final months so accounts do not create
    a full month of activity in a shortened activity window. Closed salary
    accounts transfer out any remaining balance at activity_end_date.
    """
    salary_transactions = []

    if segment_id not in SALARY_AMOUNT_RULES:
        raise ValueError(
            f"Salary account generated for invalid segment: {segment_id}"
        )

    monthly_salary = choose_monthly_salary(segment_id)
    account["_monthly_salary"] = monthly_salary

    available_balance = generate_opening_balance(
        segment_id,
        account["product_id"]
    )

    schedule_start_date = account["_activity_start_date"]
    schedule_end_date = account["_activity_end_date"]

    # Salary accounts use a stable monthly salary day, similar to payroll.
    salary_day = random.choice(SALARY_DAY_OPTIONS)

    # Use calendar-month salary cycles anchored to the account activity month.
    current_salary_cycle = schedule_start_date.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    running_balance = available_balance

    while current_salary_cycle <= schedule_end_date:
        salary_month_day = get_valid_month_day(
            current_salary_cycle.year,
            current_salary_cycle.month,
            salary_day
        )

        salary_date = current_salary_cycle.replace(
            day=salary_month_day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        # Skip months where the salary date falls outside the account's
        # activity window.
        if schedule_start_date <= salary_date <= schedule_end_date:
            salary_timestamp = assign_bank_business_time(
                salary_date,
                earliest_allowed=schedule_start_date,
                latest_allowed=schedule_end_date
            )

            # Monthly salary credit increases the available account balance.
            transaction = {
                "transaction_id": f"TR{starting_transaction_counter:06d}",
                "account_id": account["account_id"],
                "transaction_timestamp": salary_timestamp,
                "transaction_type": "Salary Credit",
                "transaction_direction": "Credit",
                "amount": monthly_salary,
                "currency": account["currency"],
                "channel": choose_channel("Salary Credit"),
                "merchant_category": None,
                "created_at": generate_created_at(salary_timestamp),
            }

            salary_transactions.append(transaction)
            starting_transaction_counter += 1

            running_balance = (
                running_balance + monthly_salary
            ).quantize(MONEY_PRECISION)

            # Build the next salary date so spending can be generated between
            # this salary credit and the next one.
            next_salary_cycle = add_one_month(current_salary_cycle)

            next_salary_month_day = get_valid_month_day(
                next_salary_cycle.year,
                next_salary_cycle.month,
                salary_day
            )

            next_salary_date = next_salary_cycle.replace(
                day=next_salary_month_day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

            spending_window_start = salary_timestamp + timedelta(seconds=1)
            normal_spending_window_end = next_salary_date - timedelta(seconds=1)

            # The final account activity window may end before the next salary
            # date, so spending must stop at activity_end_date.
            spending_window_end = min(
                normal_spending_window_end,
                schedule_end_date
            )

            actual_window_seconds = int(
                (spending_window_end - spending_window_start).total_seconds()
            )

            full_window_seconds = int(
                (normal_spending_window_end - spending_window_start).total_seconds()
            )

            if actual_window_seconds <= 0 or full_window_seconds <= 0:
                current_salary_cycle = add_one_month(current_salary_cycle)
                continue

            # Scale spending down for shortened cycles. Example: if only half
            # the normal spending window remains, generate roughly half the
            # spending budget and half the transaction count.
            window_ratio = (
                Decimal(actual_window_seconds) / Decimal(full_window_seconds)
            ).quantize(MONEY_PRECISION)

            window_ratio = min(window_ratio, Decimal("1.000"))

            full_month_spending_budget = generate_total_salary_spending_amount(
                monthly_salary,
                segment_id
            )

            monthly_spending_budget = (
                full_month_spending_budget * window_ratio
            ).quantize(MONEY_PRECISION)

            # Salary accounts cannot spend more than their available balance.
            monthly_spending_budget = min(
                monthly_spending_budget,
                running_balance
            ).quantize(MONEY_PRECISION)

            min_count, max_count = SALARY_MONTHLY_TRANSACTION_COUNT_RULES[segment_id]

            base_transaction_count = random.randint(min_count, max_count)

            transaction_count = math.ceil(
                base_transaction_count * float(window_ratio)
            )

            transaction_count = max(1, transaction_count)

            # Generate salary-funded spending transactions after the salary
            # credit and before the next salary cycle.
            for transaction_index in range(transaction_count):
                if monthly_spending_budget <= 0 or running_balance <= 0:
                    break

                transaction_timestamp = spending_window_start + timedelta(
                    seconds=random.randint(0, actual_window_seconds)
                )

                salary_spending_types_weights = [
                    spending_type["weight"]
                    for spending_type in SALARY_SPENDING_TYPES
                ]

                transaction_chosen = random.choices(
                    SALARY_SPENDING_TYPES,
                    weights=salary_spending_types_weights,
                    k=1
                )[0]

                # Spread the remaining monthly budget across the remaining
                # transactions, then randomize each amount around that average.
                remaining_transactions = transaction_count - transaction_index

                average_transaction_amount = (
                    monthly_spending_budget / Decimal(remaining_transactions)
                ).quantize(MONEY_PRECISION)

                amount_multiplier = Decimal(str(random.uniform(0.50, 1.75)))

                transaction_amount = (
                    average_transaction_amount * amount_multiplier
                ).quantize(MONEY_PRECISION)

                # Final cap protects both the monthly budget and the account
                # balance from going negative.
                transaction_amount = min(
                    transaction_amount,
                    monthly_spending_budget,
                    running_balance
                ).quantize(MONEY_PRECISION)

                if transaction_amount <= 0:
                    break

                transaction = {
                    "transaction_id": f"TR{starting_transaction_counter:06d}",
                    "account_id": account["account_id"],
                    "transaction_timestamp": transaction_timestamp,
                    "transaction_type": transaction_chosen["transaction_type"],
                    "transaction_direction": transaction_chosen["direction"],
                    "amount": transaction_amount,
                    "currency": account["currency"],
                    "channel": choose_channel(transaction_chosen["transaction_type"]),
                    "merchant_category": choose_merchant_category(
                        transaction_chosen["transaction_type"]
                    ),
                    "created_at": generate_created_at(transaction_timestamp),
                }

                salary_transactions.append(transaction)
                starting_transaction_counter += 1

                running_balance = (
                    running_balance - transaction_amount
                ).quantize(MONEY_PRECISION)

                monthly_spending_budget = (
                    monthly_spending_budget - transaction_amount
                ).quantize(MONEY_PRECISION)

        # Move to the next calendar-month salary cycle.
        current_salary_cycle = add_one_month(current_salary_cycle)

    # Closed salary accounts must end at zero, so any remaining balance is
    # transferred out at the activity end timestamp.
    if account["account_status"] == "Closed" and running_balance > 0:
        closure_amount = running_balance.quantize(MONEY_PRECISION)

        closure_transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": schedule_end_date,
            "transaction_type": "Account Closure Transfer",
            "transaction_direction": "Debit",
            "amount": closure_amount,
            "currency": account["currency"],
            "channel": "System",
            "merchant_category": None,
            "created_at": generate_created_at(schedule_end_date),
        }

        salary_transactions.append(closure_transaction)
        starting_transaction_counter += 1

        running_balance = Decimal("0.000")

    account["current_balance"] = running_balance.quantize(MONEY_PRECISION)

    return salary_transactions, starting_transaction_counter


# ============================================================
# Transaction dispatcher
# ============================================================


def generate_transactions(accounts, customers):
    customer_segment_by_id = {
        customer["customer_id"]: customer["segment_id"]
        for customer in customers
    }

    transactions = []
    transaction_counter = 1

    for account in accounts:
        segment_id = customer_segment_by_id[account["customer_id"]]

        if account["product_id"] in LOAN_LIKE_PRODUCTS:
            new_transactions, transaction_counter = generate_loan_like_transactions(
                account,
                segment_id,
                transaction_counter
            )

        elif account["product_id"] in CREDIT_CARD_PRODUCTS:
            new_transactions, transaction_counter = generate_credit_card_transactions(
                account,
                segment_id,
                transaction_counter
            )

        elif account["product_id"] == "PRD003":
            new_transactions, transaction_counter = generate_salary_account_transactions(
                account,
                segment_id,
                transaction_counter
            )

        else:
            new_transactions, transaction_counter = generate_deposit_like_transactions(
                account,
                segment_id,
                transaction_counter
            )    
        
        transactions.extend(new_transactions)

    return transactions


# ============================================================
# Balance/account update helpers
# ============================================================


def apply_transaction_to_balance(balance, transaction):
    amount = transaction["amount"]

    if transaction["transaction_direction"] == "Credit":
        return balance + amount

    if transaction["transaction_direction"] == "Debit":
        return balance - amount

    raise ValueError(
        f"Unknown transaction direction: {transaction['transaction_direction']}"
    )

def update_accounts_from_transactions(accounts, transactions):
    transactions_by_account_id = {}

    for transaction in transactions:
        account_id = transaction["account_id"]

        if account_id not in transactions_by_account_id:
            transactions_by_account_id[account_id] = []

        transactions_by_account_id[account_id].append(transaction)

    for account in accounts:
        account_transactions = transactions_by_account_id.get(
            account["account_id"],
            []
        )

        account_transactions = sorted(
            account_transactions,
            key=lambda transaction: transaction["transaction_timestamp"]
        )

        opening_balance = account["_opening_balance"]
        balance = opening_balance
        lowest_balance = opening_balance
        highest_balance = opening_balance

        for transaction in account_transactions:
            balance = apply_transaction_to_balance(balance, transaction)

            lowest_balance = min(lowest_balance, balance)
            highest_balance = max(highest_balance, balance)

        # Deposit/current/savings/salary/business accounts should not go negative.
        # If they do, increase opening balance enough to cover the lowest point.
        if account["product_id"] in DEPOSIT_LIKE_PRODUCTS and lowest_balance < 0:
            safety_buffer = Decimal("50.000")
            opening_balance_adjustment = abs(lowest_balance) + safety_buffer

            opening_balance = (
                opening_balance + opening_balance_adjustment
            ).quantize(Decimal("0.001"))

            account["_opening_balance"] = opening_balance

            balance = opening_balance

            for transaction in account_transactions:
                balance = apply_transaction_to_balance(balance, transaction)

        if account["account_status"] == "Closed":
            account["current_balance"] = Decimal("0.000")
        else:
            account["current_balance"] = balance.quantize(Decimal("0.001"))

        if account_transactions:
            latest_transaction_created_at = max(
                transaction["created_at"]
                for transaction in account_transactions
            )

            if account["account_status"] == "Active":
                account["updated_at"] = latest_transaction_created_at
            else:
                account["updated_at"] = account["_activity_end_date"]
        else:
            account["updated_at"] = account["_activity_end_date"]

    return accounts


# ============================================================
# Dataset orchestration
# ============================================================


def generate_core_dataset():
    pass


# ============================================================
# Debug/sample print helpers
# ============================================================


def print_sample_transactions_by_category(
    category_name,
    product_ids,
    accounts,
    transactions,
    products,
    max_accounts_per_product=2,
    max_transactions_per_account=25,
):
    account_by_id = {
        account["account_id"]: account
        for account in accounts
    }

    product_name_by_id = {
        product["product_id"]: product["product_name"]
        for product in products
    }

    transactions_by_account_id = {}

    for transaction in transactions:
        account_id = transaction["account_id"]

        if account_id not in transactions_by_account_id:
            transactions_by_account_id[account_id] = []

        transactions_by_account_id[account_id].append(transaction)

    print("\n" + "#" * 100)
    print(category_name)
    print("#" * 100)

    for product_id in sorted(product_ids):
        product_accounts = [
            account
            for account in accounts
            if account["product_id"] == product_id
            and account["account_id"] in transactions_by_account_id
        ]

        product_accounts = sorted(
            product_accounts,
            key=lambda account: account["account_id"]
        )

        print("\n" + "=" * 100)
        print(f"{product_id} - {product_name_by_id[product_id]}")
        print("=" * 100)

        for account in product_accounts[:max_accounts_per_product]:
            account_transactions = sorted(
                transactions_by_account_id[account["account_id"]],
                key=lambda transaction: transaction["transaction_timestamp"]
            )

            running_balance = account["_opening_balance"]

            print("\n" + "-" * 100)
            print(
                f"Account: {account['account_id']} | "
                f"Status: {account['account_status']} | "
                f"Opening Balance: {account['_opening_balance']} | "
                f"Final Balance: {account['current_balance']} | "
                f"Created: {account['created_at']} | "
                f"Updated: {account['updated_at']}"
            )
            print("-" * 100)

            print(f"{'OPENING BALANCE':<25} | {running_balance}")

            for transaction in account_transactions[:max_transactions_per_account]:
                if transaction["transaction_direction"] == "Credit":
                    running_balance += transaction["amount"]
                elif transaction["transaction_direction"] == "Debit":
                    running_balance -= transaction["amount"]
                else:
                    raise ValueError(
                        f"Unknown direction: {transaction['transaction_direction']}"
                    )

                print(
                    f"{transaction['transaction_timestamp']} | "
                    f"{transaction['transaction_type']:<20} | "
                    f"{transaction['transaction_direction']:<6} | "
                    f"{transaction['amount']:>12} | "
                    f"Balance: {running_balance:>12} | "
                    f"{transaction['channel']:<8} | "
                    f"{transaction['merchant_category']}"
                )


# ============================================================
# Audit functions
# ============================================================


def audit_accounts(accounts, customers, branches, products, max_errors=50):
    """Audit generated account records before transaction generation."""

    print("#" * 120)
    print("ACCOUNT AUDIT")
    print("#" * 120)

    valid_statuses = {"Active", "Dormant", "Closed", "Blocked"}

    customer_by_id = {
        customer["customer_id"]: customer
        for customer in customers
    }

    branch_ids = {
        branch["branch_id"]
        for branch in branches
    }

    product_ids = {
        product["product_id"]
        for product in products
    }

    max_datetime = MAX_UPDATE_DATE.replace(
        hour=23,
        minute=59,
        second=59
    )

    seen_account_ids = set()
    products_by_customer = {}

    errors = []

    account_count = len(accounts)

    duplicate_account_ids = 0
    invalid_customer_ids = 0
    invalid_branch_ids = 0
    invalid_product_ids = 0
    duplicate_customer_products = 0
    invalid_statuses = 0
    invalid_currencies = 0
    invalid_product_segment_pairs = 0
    invalid_created_dates = 0
    invalid_open_dates = 0
    invalid_activity_windows = 0
    invalid_opening_balances = 0
    invalid_current_balances = 0

    status_counts = {}
    product_counts = {}
    segment_counts = {}

    for account in accounts:
        account_id = account["account_id"]
        customer_id = account["customer_id"]
        branch_id = account["branch_id"]
        product_id = account["product_id"]
        account_status = account["account_status"]
        currency = account["currency"]
        created_at = account["created_at"]
        account_open_date = account["account_open_date"]
        activity_start_date = account["_activity_start_date"]
        activity_end_date = account["_activity_end_date"]

        opening_balance = Decimal(str(account["_opening_balance"])).quantize(
            MONEY_PRECISION
        )

        current_balance = Decimal(str(account["current_balance"])).quantize(
            MONEY_PRECISION
        )

        status_counts[account_status] = status_counts.get(account_status, 0) + 1
        product_counts[product_id] = product_counts.get(product_id, 0) + 1

        # ------------------------------------------------------------------
        # Primary key uniqueness
        # ------------------------------------------------------------------
        if account_id in seen_account_ids:
            duplicate_account_ids += 1
            errors.append(f"{account_id}: duplicate account_id")
        else:
            seen_account_ids.add(account_id)

        # ------------------------------------------------------------------
        # Foreign key checks
        # ------------------------------------------------------------------
        customer = customer_by_id.get(customer_id)

        if customer is None:
            invalid_customer_ids += 1
            errors.append(f"{account_id}: invalid customer_id {customer_id}")
            continue

        segment_id = customer["segment_id"]
        customer_created_at = customer["created_at"]

        segment_counts[segment_id] = segment_counts.get(segment_id, 0) + 1

        if branch_id not in branch_ids:
            invalid_branch_ids += 1
            errors.append(f"{account_id}: invalid branch_id {branch_id}")

        if product_id not in product_ids:
            invalid_product_ids += 1
            errors.append(f"{account_id}: invalid product_id {product_id}")
            continue

        # ------------------------------------------------------------------
        # One product per customer check
        # ------------------------------------------------------------------
        customer_products = products_by_customer.setdefault(customer_id, set())

        if product_id in customer_products:
            duplicate_customer_products += 1
            errors.append(
                f"{account_id}: customer {customer_id} received duplicate product {product_id}"
            )
        else:
            customer_products.add(product_id)

        # ------------------------------------------------------------------
        # Status and product eligibility checks
        # ------------------------------------------------------------------
        if account_status not in valid_statuses:
            invalid_statuses += 1
            errors.append(f"{account_id}: invalid account_status {account_status}")

        product_weight = PRODUCT_WEIGHTS_BY_SEGMENT[segment_id].get(product_id)

        if product_weight is None or product_weight <= 0:
            invalid_product_segment_pairs += 1
            errors.append(
                f"{account_id}: product {product_id} is not eligible for segment {segment_id}"
            )

        # ------------------------------------------------------------------
        # Currency check
        # ------------------------------------------------------------------
        allowed_currencies = CURRENCY_RULES[segment_id]["currencies"]

        if currency not in allowed_currencies:
            invalid_currencies += 1
            errors.append(
                f"{account_id}: currency {currency} is not allowed for segment {segment_id}"
            )

        # ------------------------------------------------------------------
        # Created/open date checks
        # ------------------------------------------------------------------
        if created_at < customer_created_at:
            invalid_created_dates += 1
            errors.append(
                f"{account_id}: account created_at is before customer created_at"
            )

        if created_at > max_datetime:
            invalid_created_dates += 1
            errors.append(
                f"{account_id}: account created_at is after MAX_UPDATE_DATE"
            )

        if account_open_date != created_at.date():
            invalid_open_dates += 1
            errors.append(
                f"{account_id}: account_open_date does not match created_at.date()"
            )

        # ------------------------------------------------------------------
        # Activity window checks
        # ------------------------------------------------------------------
        if activity_start_date < created_at:
            invalid_activity_windows += 1
            errors.append(
                f"{account_id}: activity_start_date is before account created_at"
            )

        if activity_end_date < activity_start_date:
            invalid_activity_windows += 1
            errors.append(
                f"{account_id}: activity_end_date is before activity_start_date"
            )

        if activity_end_date > max_datetime:
            invalid_activity_windows += 1
            errors.append(
                f"{account_id}: activity_end_date is after MAX_UPDATE_DATE"
            )

        if account_status == "Active" and activity_end_date != max_datetime:
            invalid_activity_windows += 1
            errors.append(
                f"{account_id}: Active account does not end at MAX_UPDATE_DATE"
            )

        if account_status != "Active" and activity_end_date > max_datetime:
            invalid_activity_windows += 1
            errors.append(
                f"{account_id}: non-active account ends after MAX_UPDATE_DATE"
            )

        # ------------------------------------------------------------------
        # Opening balance rules
        # ------------------------------------------------------------------
        if product_id in LOAN_LIKE_PRODUCTS:
            if opening_balance != Decimal("0.000"):
                invalid_opening_balances += 1
                errors.append(
                    f"{account_id}: loan-like product has non-zero opening balance"
                )

        elif product_id in CREDIT_CARD_PRODUCTS:
            if opening_balance != Decimal("0.000"):
                invalid_opening_balances += 1
                errors.append(
                    f"{account_id}: credit card product has non-zero opening balance"
                )

        elif product_id == "PRD003":
            if opening_balance != Decimal("0.000"):
                invalid_opening_balances += 1
                errors.append(
                    f"{account_id}: salary account has non-zero opening balance"
                )

        elif product_id in DEPOSIT_LIKE_PRODUCTS:
            min_balance, max_balance = BALANCE_LIMIT_RULES[segment_id][product_id]

            min_balance = Decimal(str(min_balance)).quantize(MONEY_PRECISION)
            max_balance = Decimal(str(max_balance)).quantize(MONEY_PRECISION)

            if opening_balance < min_balance or opening_balance > max_balance:
                invalid_opening_balances += 1
                errors.append(
                    f"{account_id}: deposit opening balance {opening_balance} "
                    f"is outside allowed range {min_balance}-{max_balance}"
                )

        # ------------------------------------------------------------------
        # Current balance pre-transaction check
        # ------------------------------------------------------------------
        if current_balance != opening_balance:
            invalid_current_balances += 1
            errors.append(
                f"{account_id}: current_balance does not match _opening_balance before transactions"
            )

    print(f"Total Accounts: {account_count}")
    print(f"Unique Account IDs: {len(seen_account_ids)}")
    print()

    print("Status Counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print()

    print("Product Counts:")
    for product_id, count in sorted(product_counts.items()):
        print(f"  {product_id}: {count}")

    print()

    print("Segment Counts:")
    for segment_id, count in sorted(segment_counts.items()):
        print(f"  {segment_id}: {count}")

    print()

    print("Validation Summary:")
    print(f"  Duplicate Account IDs: {duplicate_account_ids}")
    print(f"  Invalid Customer IDs: {invalid_customer_ids}")
    print(f"  Invalid Branch IDs: {invalid_branch_ids}")
    print(f"  Invalid Product IDs: {invalid_product_ids}")
    print(f"  Duplicate Customer Products: {duplicate_customer_products}")
    print(f"  Invalid Statuses: {invalid_statuses}")
    print(f"  Invalid Currencies: {invalid_currencies}")
    print(f"  Invalid Product-Segment Pairs: {invalid_product_segment_pairs}")
    print(f"  Invalid Created Dates: {invalid_created_dates}")
    print(f"  Invalid Open Dates: {invalid_open_dates}")
    print(f"  Invalid Activity Windows: {invalid_activity_windows}")
    print(f"  Invalid Opening Balances: {invalid_opening_balances}")
    print(f"  Invalid Current Balances: {invalid_current_balances}")

    print()

    if errors:
        print("Errors:")
        for error in errors[:max_errors]:
            print(f"  - {error}")

        if len(errors) > max_errors:
            print(f"  ... {len(errors) - max_errors} more errors")
    else:
        print("No account errors found.")

    print("#" * 120)

def print_loan_like_audit(accounts, transactions, products, customers, max_accounts_per_product=5):
    account_by_id = {
        account["account_id"]: account
        for account in accounts
    }

    product_name_by_id = {
        product["product_id"]: product["product_name"]
        for product in products
    }

    customer_segment_by_id = {
        customer["customer_id"]: customer["segment_id"]
        for customer in customers
    }

    transactions_by_account_id = {}

    for transaction in transactions:
        account_id = transaction["account_id"]

        if account_id not in transactions_by_account_id:
            transactions_by_account_id[account_id] = []

        transactions_by_account_id[account_id].append(transaction)

    loan_accounts = [
        account
        for account in accounts
        if account["product_id"] in LOAN_LIKE_PRODUCTS
    ]

    loan_accounts = sorted(
        loan_accounts,
        key=lambda account: (
            account["product_id"],
            account["account_id"]
        )
    )

    print("\n" + "#" * 120)
    print("LOAN-LIKE PRODUCT AUDIT")
    print("#" * 120)

    for product_id in sorted(LOAN_LIKE_PRODUCTS):
        product_accounts = [
            account
            for account in loan_accounts
            if account["product_id"] == product_id
        ]

        print("\n" + "=" * 120)
        print(f"{product_id} - {product_name_by_id[product_id]}")
        print(f"Total accounts: {len(product_accounts)}")
        print("=" * 120)

        for account in product_accounts[:max_accounts_per_product]:
            account_transactions = transactions_by_account_id.get(
                account["account_id"],
                []
            )

            account_transactions = sorted(
                account_transactions,
                key=lambda transaction: transaction["transaction_timestamp"]
            )

            disbursements = [
                transaction
                for transaction in account_transactions
                if transaction["transaction_type"] == "Loan Disbursement"
            ]

            repayments = [
                transaction
                for transaction in account_transactions
                if transaction["transaction_type"] == "Loan Repayment"
            ]

            invalid_transaction_types = [
                transaction
                for transaction in account_transactions
                if transaction["transaction_type"] not in {
                    "Loan Disbursement",
                    "Loan Repayment",
                    "Late Fee"
                }
            ]

            transactions_after_activity_end = [
                transaction
                for transaction in account_transactions
                if transaction["transaction_timestamp"] > account["_activity_end_date"]
            ]

            transactions_before_activity_start = [
                transaction
                for transaction in account_transactions
                if transaction["transaction_timestamp"] < account["_activity_start_date"]
            ]

            running_balance = account["_opening_balance"]

            for transaction in account_transactions:
                running_balance = apply_transaction_to_balance(
                    running_balance,
                    transaction
                )

            expected_final_balance = Decimal("0.000")

            if account["account_status"] != "Closed":
                expected_final_balance = running_balance.quantize(Decimal("0.001"))

            actual_final_balance = account["current_balance"]

            total_disbursed = sum(
                transaction["amount"]
                for transaction in disbursements
            ) if disbursements else Decimal("0.000")

            total_repaid = sum(
                transaction["amount"]
                for transaction in repayments
            ) if repayments else Decimal("0.000")

            print("\n" + "-" * 120)
            print(
                f"Account: {account['account_id']} | "
                f"Customer: {account['customer_id']} | "
                f"Segment: {customer_segment_by_id[account['customer_id']]} | "
                f"Product: {account['product_id']} - {product_name_by_id[account['product_id']]}"
            )

            print(
                f"Status: {account['account_status']} | "
                f"Opening Balance: {account['_opening_balance']} | "
                f"Final Balance: {actual_final_balance} | "
                f"Expected Balance From Transactions: {expected_final_balance}"
            )

            print(
                f"Created: {account['created_at']} | "
                f"Activity Start: {account['_activity_start_date']} | "
                f"Activity End: {account['_activity_end_date']} | "
                f"Updated: {account['updated_at']}"
            )

            print(
                f"Disbursement Count: {len(disbursements)} | "
                f"Repayment Count: {len(repayments)} | "
                f"Total Disbursed: {total_disbursed} | "
                f"Total Repaid: {total_repaid}"
            )

            print(
                f"Invalid Transaction Types: {len(invalid_transaction_types)} | "
                f"Transactions Before Activity Start: {len(transactions_before_activity_start)} | "
                f"Transactions After Activity End: {len(transactions_after_activity_end)}"
            )

            if len(disbursements) != 1:
                print("WARNING: loan account does not have exactly one disbursement")

            if invalid_transaction_types:
                print("WARNING: found non-loan transaction types inside loan account")

            if transactions_after_activity_end:
                print("WARNING: found transactions after activity end date")

            if account["account_status"] != "Closed" and actual_final_balance > 0:
                print("WARNING: active/dormant/frozen loan ended positive")

            if account["account_status"] == "Closed" and actual_final_balance != Decimal("0.000"):
                print("WARNING: closed loan balance is not zero")

            print("-" * 120)
            print(f"{'TIMESTAMP':<22} | {'TYPE':<18} | {'DIR':<6} | {'AMOUNT':>14} | {'RUNNING BALANCE':>18} | CHANNEL")
            print("-" * 120)

            running_balance = account["_opening_balance"]

            for transaction in account_transactions:
                running_balance = apply_transaction_to_balance(
                    running_balance,
                    transaction
                )

                print(
                    f"{str(transaction['transaction_timestamp']):<22} | "
                    f"{transaction['transaction_type']:<18} | "
                    f"{transaction['transaction_direction']:<6} | "
                    f"{transaction['amount']:>14} | "
                    f"{running_balance:>18} | "
                    f"{transaction['channel']}"
                )

def print_credit_card_audit(accounts, transactions, customers, max_accounts=10):
    allowed_card_transaction_types = {
        "Card Purchase",
        "Card Payment",
        "Late Fee",
        "Interest Charge",
        "Cash Advance",
        "Cash Advance Fee",
    }

    expected_direction_by_type = {
        "Card Purchase": "Debit",
        "Cash Advance": "Debit",
        "Cash Advance Fee": "Debit",
        "Late Fee": "Debit",
        "Interest Charge": "Debit",
        "Card Payment": "Credit",
    }

    customer_segment_by_id = {
        customer["customer_id"]: customer["segment_id"]
        for customer in customers
    }

    transactions_by_account_id = {}

    for transaction in transactions:
        account_id = transaction["account_id"]

        if account_id not in transactions_by_account_id:
            transactions_by_account_id[account_id] = []

        transactions_by_account_id[account_id].append(transaction)

    credit_card_accounts = [
        account
        for account in accounts
        if account["product_id"] in CREDIT_CARD_PRODUCTS
    ]

    credit_card_accounts = sorted(
        credit_card_accounts,
        key=lambda account: account["account_id"]
    )

    print("\n" + "#" * 140)
    print("CREDIT CARD AUDIT")
    print("#" * 140)

    for account in credit_card_accounts[:max_accounts]:
        account_transactions = transactions_by_account_id.get(
            account["account_id"],
            []
        )

        account_transactions = sorted(
            account_transactions,
            key=lambda transaction: transaction["transaction_timestamp"]
        )

        running_balance = account["_opening_balance"]
        max_debt_balance = running_balance

        purchases = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Card Purchase"
        ]

        cash_advances = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Cash Advance"
        ]

        cash_advance_fees = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Cash Advance Fee"
        ]

        payments = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Card Payment"
        ]

        late_fees = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Late Fee"
        ]

        interest_charges = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Interest Charge"
        ]

        invalid_transaction_types = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] not in allowed_card_transaction_types
        ]

        invalid_transaction_directions = [
            transaction for transaction in account_transactions
            if (
                transaction["transaction_type"] in expected_direction_by_type
                and transaction["transaction_direction"]
                != expected_direction_by_type[transaction["transaction_type"]]
            )
        ]

        transactions_before_activity_start = [
            transaction for transaction in account_transactions
            if transaction["transaction_timestamp"] < account["_activity_start_date"]
        ]

        transactions_after_activity_end = [
            transaction for transaction in account_transactions
            if transaction["transaction_timestamp"] > account["_activity_end_date"]
        ]

        print("\n" + "=" * 140)
        print(
            f"Account: {account['account_id']} | "
            f"Customer: {account['customer_id']} | "
            f"Segment: {customer_segment_by_id[account['customer_id']]} | "
            f"Status: {account['account_status']}"
        )

        print(
            f"Opening Balance: {account['_opening_balance']} | "
            f"Final Balance: {account['current_balance']} | "
            f"Credit Limit: {account.get('_credit_limit', 'MISSING')}"
        )

        print(
            f"Created: {account['created_at']} | "
            f"Activity Start: {account['_activity_start_date']} | "
            f"Activity End: {account['_activity_end_date']} | "
            f"Updated: {account['updated_at']}"
        )

        print(
            f"Purchases: {len(purchases)} | "
            f"Cash Advances: {len(cash_advances)} | "
            f"Cash Advance Fees: {len(cash_advance_fees)} | "
            f"Payments: {len(payments)} | "
            f"Late Fees: {len(late_fees)} | "
            f"Interest Charges: {len(interest_charges)}"
        )

        print(
            f"Invalid Types: {len(invalid_transaction_types)} | "
            f"Invalid Directions: {len(invalid_transaction_directions)} | "
            f"Before Activity Start: {len(transactions_before_activity_start)} | "
            f"After Activity End: {len(transactions_after_activity_end)}"
        )

        print("-" * 140)
        print(
            f"{'TIMESTAMP':<22} | "
            f"{'TYPE':<18} | "
            f"{'DIR':<6} | "
            f"{'AMOUNT':>12} | "
            f"{'RUNNING BALANCE':>18} | "
            f"{'CHANNEL':<8} | "
            f"{'MERCHANT':<18} | "
            f"WARNING"
        )
        print("-" * 140)

        for transaction in account_transactions:
            before_balance = running_balance
            running_balance = apply_transaction_to_balance(
                running_balance,
                transaction
            )

            if running_balance < max_debt_balance:
                max_debt_balance = running_balance

            warnings = []

            transaction_type = transaction["transaction_type"]
            transaction_direction = transaction["transaction_direction"]

            if transaction_type not in allowed_card_transaction_types:
                warnings.append("INVALID TYPE")

            if (
                transaction_type in expected_direction_by_type
                and transaction_direction != expected_direction_by_type[transaction_type]
            ):
                warnings.append("INVALID DIRECTION")

            if transaction["transaction_timestamp"] < account["_activity_start_date"]:
                warnings.append("BEFORE ACTIVITY START")

            if transaction["transaction_timestamp"] > account["_activity_end_date"]:
                warnings.append("AFTER ACTIVITY END")

            if (
                transaction_type == "Card Payment"
                and before_balance < 0
                and transaction["amount"] > abs(before_balance)
            ):
                warnings.append("PAYMENT EXCEEDS OWED BALANCE")

            credit_limit = account.get("_credit_limit")

            if (
                credit_limit is not None
                and running_balance < 0
                and abs(running_balance) > credit_limit
            ):
                warnings.append("EXCEEDS CREDIT LIMIT")

            warning_text = ", ".join(warnings)

            print(
                f"{str(transaction['transaction_timestamp']):<22} | "
                f"{transaction_type:<18} | "
                f"{transaction_direction:<6} | "
                f"{transaction['amount']:>12} | "
                f"{running_balance:>18} | "
                f"{transaction['channel']:<8} | "
                f"{str(transaction['merchant_category']):<18} | "
                f"{warning_text}"
            )

        print("-" * 140)
        print(
            f"Computed Final Balance: {running_balance} | "
            f"Stored Final Balance: {account['current_balance']} | "
            f"Max Debt Reached: {abs(max_debt_balance)}"
        )
        
def print_salary_account_audit(accounts, transactions, customers, max_accounts=10):
    customer_segment_by_id = {
        customer["customer_id"]: customer["segment_id"]
        for customer in customers
    }

    transactions_by_account_id = {}

    for transaction in transactions:
        account_id = transaction["account_id"]

        if account_id not in transactions_by_account_id:
            transactions_by_account_id[account_id] = []

        transactions_by_account_id[account_id].append(transaction)

    salary_accounts = [
        account
        for account in accounts
        if account["product_id"] == "PRD003"
    ]

    salary_accounts = sorted(
        salary_accounts,
        key=lambda account: account["account_id"]
    )

    print("\n" + "#" * 120)
    print("SALARY ACCOUNT AUDIT")
    print("#" * 120)

    for account in salary_accounts[:max_accounts]:
        account_transactions = transactions_by_account_id.get(
            account["account_id"],
            []
        )

        account_transactions = sorted(
            account_transactions,
            key=lambda transaction: transaction["transaction_timestamp"]
        )

        running_balance = account["_opening_balance"]

        salary_credits = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] == "Salary Credit"
        ]

        debit_transactions = [
            transaction for transaction in account_transactions
            if transaction["transaction_direction"] == "Debit"
        ]

        invalid_transaction_types = [
            transaction for transaction in account_transactions
            if transaction["transaction_type"] not in {
                "Salary Credit",
                "ATM Withdrawal",
                "POS Purchase",
                "Bill Payment",
                "Transfer Out",
                "Account Closure Transfer"
            }
        ]

        transactions_after_activity_end = [
            transaction for transaction in account_transactions
            if transaction["transaction_timestamp"] > account["_activity_end_date"]
        ]

        went_negative = False
        lowest_balance = running_balance

        for transaction in account_transactions:
            running_balance = apply_transaction_to_balance(
                running_balance,
                transaction
            )

            if running_balance < 0:
                went_negative = True

            lowest_balance = min(lowest_balance, running_balance)

            transactions_before_activity_start = [
                transaction for transaction in account_transactions
                if transaction["transaction_timestamp"] < account["_activity_start_date"]
            ]

        print("\n" + "=" * 120)
        print(
            f"Account: {account['account_id']} | "
            f"Customer: {account['customer_id']} | "
            f"Segment: {customer_segment_by_id[account['customer_id']]} | "
            f"Status: {account['account_status']}"
        )

        print(
            f"Opening Balance: {account['_opening_balance']} | "
            f"Final Balance: {account['current_balance']} | "
            f"Monthly Salary: {account.get('_monthly_salary', 'MISSING')} | "
            f"Lowest Balance: {lowest_balance}"
        )

        print(
            f"Before Activity Start: {len(transactions_before_activity_start)} | "
            f"Created: {account['created_at']} | "
            f"Activity Start: {account['_activity_start_date']} | "
            f"Activity End: {account['_activity_end_date']} | "
            f"Updated: {account['updated_at']}"
        )

        print(
            f"Salary Credits: {len(salary_credits)} | "
            f"Debit Transactions: {len(debit_transactions)} | "
            f"Invalid Types: {len(invalid_transaction_types)} | "
            f"After Activity End: {len(transactions_after_activity_end)} | "
            f"Went Negative: {went_negative}"
        )

        if account.get("_monthly_salary") == "MISSING":
            print("WARNING: missing _monthly_salary")

        if went_negative:
            print("WARNING: salary account went negative")

        if invalid_transaction_types:
            print("WARNING: invalid transaction types found")

        if transactions_after_activity_end:
            print("WARNING: transactions after activity end found")

        if account["account_status"] == "Closed" and account["current_balance"] != Decimal("0.000"):
            print("WARNING: closed salary account did not end at 0")

        if transactions_before_activity_start:
            print("WARNING: transactions before activity start found")
        print("-" * 120)
        print(
            f"{'TIMESTAMP':<22} | "
            f"{'TYPE':<18} | "
            f"{'DIR':<6} | "
            f"{'AMOUNT':>12} | "
            f"{'RUNNING BALANCE':>18} | "
            f"CHANNEL | MERCHANT"
        )
        print("-" * 120)

        running_balance = account["_opening_balance"]

        for transaction in account_transactions:
            running_balance = apply_transaction_to_balance(
                running_balance,
                transaction
            )

            warning = ""

            if running_balance < 0:
                warning = "  <-- WARNING: negative balance"

            print(
                f"{str(transaction['transaction_timestamp']):<22} | "
                f"{transaction['transaction_type']:<18} | "
                f"{transaction['transaction_direction']:<6} | "
                f"{transaction['amount']:>12} | "
                f"{running_balance:>18} | "
                f"{transaction['channel']:<8} | "
                f"{transaction['merchant_category']}"
                f"{warning}"
            )

def print_deposit_like_audit(accounts, transactions, max_accounts=10):
    print("#" * 120)
    print("DEPOSIT-LIKE ACCOUNT AUDIT")
    print("#" * 120)

    deposit_accounts = [
        account for account in accounts
        if account["product_id"] in DEPOSIT_LIKE_PRODUCTS
    ]

    for account in deposit_accounts[:max_accounts]:
        account_id = account["account_id"]
        product_id = account["product_id"]
        account_status = account["account_status"]

        account_created_at = get_account_created_at(account)

        account_transactions = [
            transaction for transaction in transactions
            if transaction["account_id"] == account_id
        ]

        account_transactions.sort(
            key=lambda transaction: transaction["transaction_timestamp"]
        )

        opening_balance = Decimal(str(account["_opening_balance"])).quantize(
            MONEY_PRECISION
        )

        stored_final_balance = Decimal(str(account["current_balance"])).quantize(
            MONEY_PRECISION
        )

        running_balance = Decimal("0.000")
        lowest_balance = running_balance

        invalid_types = 0
        invalid_directions = 0
        before_activity_start = 0
        after_activity_end = 0
        went_negative = False

        debit_count = 0
        credit_count = 0

        opening_deposit_count = 0
        opening_deposit_amount_valid = False
        opening_deposit_timestamp_valid = False

        closure_transfer_count = 0
        closure_transfer_timestamp_valid = True

        for transaction in account_transactions:
            transaction_type = transaction["transaction_type"]
            transaction_direction = transaction["transaction_direction"]
            transaction_timestamp = transaction["transaction_timestamp"]

            transaction_amount = Decimal(str(transaction["amount"])).quantize(
                MONEY_PRECISION
            )

            if transaction_type not in DEPOSIT_ALLOWED_TRANSACTION_TYPES[product_id]:
                invalid_types += 1

            expected_direction = DEPOSIT_EXPECTED_DIRECTIONS.get(transaction_type)

            if expected_direction != transaction_direction:
                invalid_directions += 1

            if transaction_type == "Opening Deposit":
                opening_deposit_count += 1

                if transaction_amount == opening_balance:
                    opening_deposit_amount_valid = True

                if transaction_timestamp == account["_activity_start_date"]:
                    opening_deposit_timestamp_valid = True

            else:
                if transaction_timestamp < account["_activity_start_date"]:
                    before_activity_start += 1

            if transaction_timestamp > account["_activity_end_date"]:
                after_activity_end += 1

            if transaction_type == "Account Closure Transfer":
                closure_transfer_count += 1

                if transaction_timestamp != account["_activity_end_date"]:
                    closure_transfer_timestamp_valid = False

            if transaction_direction == "Credit":
                running_balance = (
                    running_balance + transaction_amount
                ).quantize(MONEY_PRECISION)

                credit_count += 1

            elif transaction_direction == "Debit":
                running_balance = (
                    running_balance - transaction_amount
                ).quantize(MONEY_PRECISION)

                debit_count += 1

            if running_balance < 0:
                went_negative = True

            lowest_balance = min(lowest_balance, running_balance)

        computed_final_balance = running_balance.quantize(MONEY_PRECISION)

        final_balance_matches = (
            stored_final_balance == computed_final_balance
        )

        opening_deposit_valid = (
            opening_deposit_count == 1
            and opening_deposit_amount_valid
            and opening_deposit_timestamp_valid
        )

        closed_final_balance_valid = True
        closed_closure_handling_valid = True

        if account_status == "Closed":
            closed_final_balance_valid = (
                stored_final_balance == Decimal("0.000")
            )

            closed_closure_handling_valid = (
                closed_final_balance_valid
                and closure_transfer_count <= 1
                and closure_transfer_timestamp_valid
            )

        print("\n" + "=" * 120)
        print(
            f"Account: {account_id} | "
            f"Product: {product_id} | "
            f"Status: {account_status}"
        )

        print(
            f"Opening Balance: {opening_balance} | "
            f"Stored Final Balance: {stored_final_balance} | "
            f"Computed Final Balance: {computed_final_balance} | "
            f"Lowest Balance: {lowest_balance}"
        )

        print(
            f"Transactions: {len(account_transactions)} | "
            f"Credits: {credit_count} | "
            f"Debits: {debit_count} | "
            f"Opening Deposits: {opening_deposit_count} | "
            f"Closure Transfers: {closure_transfer_count}"
        )

        print(
            f"Invalid Types: {invalid_types} | "
            f"Invalid Directions: {invalid_directions} | "
            f"Before Activity Start: {before_activity_start} | "
            f"After Activity End: {after_activity_end} | "
            f"Went Negative: {went_negative} | "
            f"Final Balance Matches: {final_balance_matches}"
        )

        print(
            f"Opening Deposit Valid: {opening_deposit_valid} | "
            f"Opening Deposit Amount Valid: {opening_deposit_amount_valid} | "
            f"Opening Deposit Timestamp Valid: {opening_deposit_timestamp_valid}"
        )

        if "_deposit_active_months" in account:
            print(
                f"Active Months: {account.get('_deposit_active_months')} | "
                f"Expected Count Range: {account.get('_deposit_expected_count_range')} | "
                f"Generated Count: {account.get('_deposit_generated_count')}"
            )
        else:
            active_months = estimate_active_months(
                account["_activity_start_date"],
                account["_activity_end_date"]
            )

            print(f"Active Months: {active_months}")

        if account_status == "Closed":
            print(
                f"Closed Final Balance Valid: {closed_final_balance_valid} | "
                f"Closed Closure Handling Valid: {closed_closure_handling_valid} | "
                f"Closure Timestamp Valid: {closure_transfer_timestamp_valid}"
            )

        print("-" * 120)
        print(
            f"{'TIMESTAMP':<22} | "
            f"{'TYPE':<25} | "
            f"{'DIR':<6} | "
            f"{'AMOUNT':>12} | "
            f"{'CHANNEL':<8} | "
            f"{'MERCHANT'}"
        )
        print("-" * 120)

        for transaction in account_transactions[:40]:
            print(
                f"{str(transaction['transaction_timestamp']):<22} | "
                f"{transaction['transaction_type']:<25} | "
                f"{transaction['transaction_direction']:<6} | "
                f"{str(transaction['amount']):>12} | "
                f"{str(transaction['channel']):<8} | "
                f"{transaction['merchant_category']}"
            )

        if len(account_transactions) > 40:
            print(f"... {len(account_transactions) - 40} more transactions")

if __name__ == "__main__":
    from scripts.generate_crm_data import generate_crm_dataset

    branches = generate_branches()
    products = generate_products()

    crm_dataset = generate_crm_dataset(200)

    accounts = generate_accounts(
        crm_dataset["customers"],
        branches,
        products
    )

    transactions = generate_transactions(accounts, crm_dataset["customers"])

    update_accounts_from_transactions(accounts, transactions)
    print_salary_account_audit(accounts, transactions, crm_dataset["customers"])