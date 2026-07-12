import random
from datetime import datetime, timedelta
from decimal import Decimal
import calendar
import math

MONEY_PRECISION = Decimal("0.001")

MAX_UPDATE_DATE = datetime(2026, 6, 30)

BANK_BUSINESS_START_HOUR = 8
BANK_BUSINESS_END_HOUR = 16

BANK_WEEKEND_DAYS = {4, 5}  # Friday=4, Saturday=5 in Python datetime.weekday()

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
    # This value is inserted as an "Opening Deposit" credit transaction near account creation.
    # Loans, credit cards, and salary accounts start from zero and build balances from their own schedules.
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

MERCHANT_CATEGORIES_BY_TRANSACTION_TYPE = {
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

    "Client Payment": [
        "Business Services",
        "Retail",
        "Online Services",
    ],

    "POS Settlement": [
        "Retail",
        "Restaurants",
        "Fuel",
        "Groceries",
        "Hotels",
    ],
}

CHANNEL_RULES_BY_TRANSACTION_TYPE = {
    "Cash Deposit": [
        {"channel": "Branch", "weight": 70},
        {"channel": "ATM", "weight": 30},
    ],

    "Deposit": [
        {"channel": "Branch", "weight": 75},
        {"channel": "ATM", "weight": 25},
    ],

    "ATM Withdrawal": [
        {"channel": "ATM", "weight": 100},
    ],

    "Withdrawal": [
        {"channel": "ATM", "weight": 70},
        {"channel": "Branch", "weight": 30},
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

    "POS Purchase": [
        {"channel": "POS", "weight": 85},
        {"channel": "Online", "weight": 15},
    ],

    "Customer Payment": [
        {"channel": "Online", "weight": 55},
        {"channel": "Mobile", "weight": 30},
        {"channel": "Branch", "weight": 15},
    ],

    "POS Settlement": [
        {"channel": "System", "weight": 100},
    ],

    "Supplier Payment": [
        {"channel": "Online", "weight": 55},
        {"channel": "Mobile", "weight": 25},
        {"channel": "Branch", "weight": 20},
    ],

    "Payroll Payment": [
        {"channel": "Online", "weight": 60},
        {"channel": "System", "weight": 30},
        {"channel": "Branch", "weight": 10},
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

    "Refund": [
        {"channel": "POS", "weight": 50},
        {"channel": "Online", "weight": 30},
        {"channel": "System", "weight": 20},
    ],

    "Cash Advance": [
        {"channel": "ATM", "weight": 80},
        {"channel": "Branch", "weight": 20},
    ],

    "Late Fee": [
        {"channel": "System", "weight": 100},
    ],
}

GENERIC_TRANSACTION_AMOUNT_RULES = {
    # Amount ranges for generic deposit-style account transactions.
    # Loans, credit cards, and salary accounts use their own schedule-based
    # generation logic instead of these generic random ranges.
    "SEG001": {
        "Cash Deposit": [20, 3_000],
        "Transfer In": [10, 5_000],
        "ATM Withdrawal": [10, 500],
        "POS Purchase": [2, 250],
        "Transfer Out": [10, 3_000],
        "Bill Payment": [10, 500],
        "Fee": [1, 25],
        "Deposit": [20, 5_000],
        "Interest Credit": [1, 50],
        "Withdrawal": [10, 1_000],
        "Customer Payment": [50, 10_000],
        "POS Settlement": [100, 15_000],
        "Supplier Payment": [100, 15_000],
        "Payroll Payment": [500, 20_000],
    },

    "SEG002": {
        "Cash Deposit": [100, 10_000],
        "Transfer In": [100, 20_000],
        "ATM Withdrawal": [20, 1_000],
        "POS Purchase": [5, 1_000],
        "Transfer Out": [100, 15_000],
        "Bill Payment": [20, 1_500],
        "Fee": [2, 50],
        "Deposit": [100, 20_000],
        "Interest Credit": [5, 300],
        "Withdrawal": [50, 3_000],
        "Customer Payment": [100, 25_000],
        "POS Settlement": [100, 30_000],
        "Supplier Payment": [100, 30_000],
        "Payroll Payment": [1_000, 50_000],
    },

    "SEG003": {
        "Cash Deposit": [100, 25_000],
        "Transfer In": [100, 50_000],
        "ATM Withdrawal": [20, 1_000],
        "POS Purchase": [5, 1_000],
        "Transfer Out": [100, 50_000],
        "Bill Payment": [50, 5_000],
        "Fee": [5, 200],
        "Deposit": [100, 30_000],
        "Interest Credit": [5, 500],
        "Withdrawal": [50, 5_000],
        "Customer Payment": [50, 20_000],
        "POS Settlement": [100, 30_000],
        "Supplier Payment": [100, 30_000],
        "Payroll Payment": [500, 50_000],
    },

    "SEG004": {
        "Cash Deposit": [1_000, 100_000],
        "Transfer In": [1_000, 500_000],
        "ATM Withdrawal": [100, 5_000],
        "POS Purchase": [50, 10_000],
        "Transfer Out": [1_000, 500_000],
        "Bill Payment": [500, 50_000],
        "Fee": [20, 1_000],
        "Deposit": [1_000, 250_000],
        "Interest Credit": [50, 5_000],
        "Withdrawal": [500, 20_000],
        "Customer Payment": [1_000, 250_000],
        "POS Settlement": [1_000, 300_000],
        "Supplier Payment": [1_000, 500_000],
        "Payroll Payment": [5_000, 500_000],
    },

    "SEG005": {
        "Cash Deposit": [1_000, 100_000],
        "Transfer In": [1_000, 250_000],
        "ATM Withdrawal": [100, 2_000],
        "POS Purchase": [20, 3_000],
        "Transfer Out": [1_000, 150_000],
        "Bill Payment": [100, 5_000],
        "Fee": [5, 250],
        "Deposit": [1_000, 250_000],
        "Interest Credit": [50, 5_000],
        "Withdrawal": [500, 20_000],
        "Customer Payment": [1_000, 100_000],
        "POS Settlement": [1_000, 100_000],
        "Supplier Payment": [1_000, 150_000],
        "Payroll Payment": [5_000, 150_000],
    },
}

GENERIC_TRANSACTION_COUNT_RULES = {
    # Transaction count ranges for generic deposit-style accounts only.
    # Salary accounts, loans, mortgages, and credit cards generate transactions
    # through specialized schedule/cycle logic instead of this generic count rule.

    # SEG001 - Retail: normal individual customers
    "SEG001": {
        "PRD001": {  # Current Account
            "Active": [12, 45],
            "Dormant": [0, 3],
            "Blocked": [0, 2],
            "Closed": [0, 6],
        },
        "PRD002": {  # Savings Account
            "Active": [2, 16],
            "Dormant": [0, 2],
            "Blocked": [0, 1],
            "Closed": [0, 4],
        },
        "PRD004": {  # Business Account - rare retail edge case
            "Active": [20, 80],
            "Dormant": [0, 4],
            "Blocked": [0, 2],
            "Closed": [0, 8],
        },
    },

    # SEG002 - Premium: higher-value individual customers
    "SEG002": {
        "PRD001": {  # Current Account
            "Active": [20, 70],
            "Dormant": [0, 4],
            "Blocked": [0, 2],
            "Closed": [0, 8],
        },
        "PRD002": {  # Savings Account
            "Active": [4, 25],
            "Dormant": [0, 3],
            "Blocked": [0, 1],
            "Closed": [0, 5],
        },
        "PRD004": {  # Business Account - business owner edge case
            "Active": [30, 120],
            "Dormant": [0, 5],
            "Blocked": [0, 2],
            "Closed": [0, 10],
        },
    },

    # SEG003 - SME: small/medium business customers
    "SEG003": {
        "PRD001": {  # Current Account
            "Active": [25, 100],
            "Dormant": [0, 5],
            "Blocked": [0, 2],
            "Closed": [0, 10],
        },
        "PRD002": {  # Savings Account
            "Active": [3, 20],
            "Dormant": [0, 3],
            "Blocked": [0, 1],
            "Closed": [0, 5],
        },
        "PRD004": {  # Business Account
            "Active": [50, 220],
            "Dormant": [0, 8],
            "Blocked": [0, 3],
            "Closed": [0, 15],
        },
    },

    # SEG004 - Corporate: large business/institution customers
    "SEG004": {
        "PRD001": {  # Current Account
            "Active": [50, 220],
            "Dormant": [0, 8],
            "Blocked": [0, 3],
            "Closed": [0, 15],
        },
        "PRD002": {  # Savings Account
            "Active": [5, 35],
            "Dormant": [0, 3],
            "Blocked": [0, 1],
            "Closed": [0, 6],
        },
        "PRD004": {  # Business Account
            "Active": [100, 500],
            "Dormant": [0, 12],
            "Blocked": [0, 4],
            "Closed": [0, 25],
        },
    },

    # SEG005 - Private: wealthy individual customers
    "SEG005": {
        "PRD001": {  # Current Account
            "Active": [25, 90],
            "Dormant": [0, 5],
            "Blocked": [0, 2],
            "Closed": [0, 10],
        },
        "PRD002": {  # Savings Account
            "Active": [5, 40],
            "Dormant": [0, 3],
            "Blocked": [0, 1],
            "Closed": [0, 6],
        },
        "PRD004": {  # Business Account - business owner/private client
            "Active": [40, 160],
            "Dormant": [0, 6],
            "Blocked": [0, 2],
            "Closed": [0, 12],
        },
    },
}

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

salary_spending_types = [
    {"transaction_type": "POS Purchase", "direction": "Debit", "weight": 35},
    {"transaction_type": "ATM Withdrawal", "direction": "Debit", "weight": 25},
    {"transaction_type": "Bill Payment", "direction": "Debit", "weight": 20},
    {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 20},
]

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

LOAN_LIKE_PRODUCTS = {"PRD005", "PRD006", "PRD008"}
CREDIT_CARD_PRODUCTS = {"PRD007"}
DEPOSIT_LIKE_PRODUCTS = {"PRD001", "PRD002", "PRD004"}
SALARY_LIKE_PRODUCTS = {"PRD003"}

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
    at account creation time. Loans, credit cards, and salary accounts start
    from zero because their balances are built from specialized schedules.
    """
    if (
        product_id in LOAN_LIKE_PRODUCTS
        or product_id in CREDIT_CARD_PRODUCTS
        or product_id == SALARY_LIKE_PRODUCTS
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

def generate_transaction_timestamp(account):
    min_datetime = account["_activity_start_date"]
    max_datetime = account["_activity_end_date"]

    total_seconds = int((max_datetime - min_datetime).total_seconds())

    if total_seconds <= 0:
        raise ValueError(
        f"Invalid activity window for account {account['account_id']}: "
        f"start {min_datetime} is after end {max_datetime}"
    )

    return min_datetime + timedelta(
        seconds=random.randint(0, total_seconds)
    )

def generate_created_at(transaction_timestamp):
    return transaction_timestamp + timedelta(
        minutes=random.randint(0, 10),
        seconds=random.randint(0, 59),
    )

def generate_transaction_amount(segment_id, product_id, transaction_type):
    segment_rules = GENERIC_TRANSACTION_AMOUNT_RULES.get(segment_id)

    if segment_rules is None:
        raise ValueError(f"No transaction amount rules for segment {segment_id}")

    if transaction_type not in segment_rules:
        raise ValueError(
            f"No amount rule for segment {segment_id}, "
            f"product {product_id}, transaction type {transaction_type}"
        )

    min_amount, max_amount = segment_rules[transaction_type]

    amount_in_thousandths = random.randint(
        min_amount * 1000,
        max_amount * 1000
    )

    return Decimal(amount_in_thousandths) / Decimal("1000")

def generate_transaction_count(segment_id, product_id, account_status):
    limits = GENERIC_TRANSACTION_COUNT_RULES[segment_id][product_id][account_status]

    if not limits:
        raise ValueError(
            f"Invalid transaction count rule for segment {segment_id}, "
            f"product {product_id}, status {account_status}"
        )

    min_count, max_count = limits

    return random.randint(min_count, max_count)

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

def generate_loan_like_transactions(account, segment_id, starting_transaction_counter):
    # If a loan account is closed, force final repayment so the ending balance becomes zero.
    # Dormant and Blocked loans are not forced to settle; they may keep an outstanding balance
    # because their activity stops before the full loan term finishes.

    loan_transactions = []

    schedule_end_date = account["_activity_end_date"]

    # 1. Generate original loan amount
    disbursement_amount = generate_loan_principal_amount(
        segment_id,
        account["product_id"],
    ).quantize(Decimal("0.001"))

    outstanding_balance = disbursement_amount

    # 3. Disbursement happens near account opening
    disbursement_date = account["_activity_start_date"] + timedelta(
        days=random.randint(0, 3)
    )

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

    # 4. Choose loan term and monthly repayment
    loan_term_months = choose_loan_term_months(account["product_id"])

    monthly_repayment_amount = (
        disbursement_amount / Decimal(loan_term_months)
    ).quantize(Decimal("0.001"))

    # 5. Generate monthly repayments, but never past schedule_end_date
    for i in range(1, loan_term_months + 1):
        payment_date = disbursement_date + timedelta(days=30 * i)

        if payment_date > schedule_end_date:
            break

        if outstanding_balance <= 0:
            break

        payment_timestamp = assign_random_business_time(
            payment_date,
            earliest_allowed=account["_activity_start_date"],
            latest_allowed=schedule_end_date)

        repayment_amount = min(
            monthly_repayment_amount,
            outstanding_balance
        ).quantize(Decimal("0.001"))

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
                ).quantize(Decimal("0.001"))

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

    # 6. If account is closed force final settlement
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

def choose_credit_card_limit(segment_id):
    min_limit, max_limit = CREDIT_CARD_LIMIT_RULES[segment_id]

    amount_in_thousandths = random.randint(
        min_limit * 1000,
        max_limit * 1000
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def generate_card_purchase_amount(credit_limit):
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
    max_advance = max(Decimal("20.000"), credit_limit * Decimal("0.20"))

    amount_in_thousandths = random.randint(
        20 * 1000,
        int(max_advance * 1000)
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def calculate_minimum_card_payment(statement_balance, segment_id):
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
    min_fee, max_fee = CARD_LATE_FEE_RULES[segment_id]
    fee = Decimal(random.randint(min_fee, max_fee)).quantize(Decimal("0.001"))

    return fee

def calculate_card_interest_charge(unpaid_statement_balance, segment_id):
    if unpaid_statement_balance <= 0:
        return Decimal("0.000")

    interest_rate = CARD_INTEREST_RATE_RULES[segment_id]

    interest = (
        unpaid_statement_balance * interest_rate
    ).quantize(Decimal("0.001"))

    return interest

def calculate_cash_advance_fee(cash_advance_amount, segment_id):
    rule = CARD_CASH_ADVANCE_FEE_RULES[segment_id]

    fee = max(
        cash_advance_amount * rule["rate"],
        rule["min"]
    ).quantize(Decimal("0.001"))

    return fee

def generate_credit_card_transactions(account, segment_id, starting_transaction_counter):
    card_transactions = []

    schedule_start_date = account["_activity_start_date"]
    schedule_end_date = account["_activity_end_date"]

    credit_limit = choose_credit_card_limit(segment_id)
    account["_credit_limit"] = credit_limit

    outstanding_balance = Decimal("0.000")

    current_cycle_date = schedule_start_date

    while current_cycle_date <= schedule_end_date:
        cycle_start_date = current_cycle_date

        cycle_end_date = min(
          cycle_start_date + timedelta(days = 30),
          schedule_end_date  
        ) 

        payment_date = min(
            cycle_start_date + timedelta(days= random.randint(20,30)),
            cycle_end_date
        )

        payment_timestamp = assign_random_business_time(
            payment_date,
            earliest_allowed=cycle_start_date,
            latest_allowed=cycle_end_date
        )

        is_final_closed_cycle = (
            account["account_status"] == "Closed" and cycle_end_date == schedule_end_date
        )

        purchase_cutoff_timestamp = payment_timestamp

        if is_final_closed_cycle:
            purchase_cutoff_timestamp = schedule_end_date

        purchase_window_seconds = int(
            (purchase_cutoff_timestamp - cycle_start_date).total_seconds()
        )

        cycle_days = max(1, (cycle_end_date - cycle_start_date).days + 1)

        if cycle_days < 7:
            purchase_count = random.randint(0, 3)
        elif cycle_days < 15:
            purchase_count = random.randint(1, 6)
        else:
            purchase_count = random.randint(3, 12)

        for _ in range(purchase_count):
            if purchase_window_seconds <= 0:
                break
            
            if outstanding_balance >= credit_limit:
                break

            available_credit = (
                credit_limit - outstanding_balance
            ).quantize(Decimal("0.001"))

            if available_credit <= 0:
                break

            purchase_amount = generate_card_purchase_amount(credit_limit)

            if purchase_amount > available_credit:
                purchase_amount = available_credit

            purchase_amount = purchase_amount.quantize(Decimal("0.001"))

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
            ).quantize(Decimal("0.001"))

        available_credit = (
            credit_limit - outstanding_balance
        ).quantize(Decimal("0.001"))

        if (
            purchase_window_seconds > 0
            and available_credit > 0
            and random.random() < CARD_CASH_ADVANCE_PROBABILITY_BY_SEGMENT[segment_id]
        ):
            cash_advance_amount = generate_cash_advance_amount(credit_limit)

            cash_advance_amount = min(
                cash_advance_amount,
                available_credit
            ).quantize(Decimal("0.001"))

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
            ).quantize(Decimal("0.001"))

            cash_advance_fee_amount = calculate_cash_advance_fee(
                cash_advance_amount,
                segment_id
            )

            available_credit = (
                credit_limit - outstanding_balance
            ).quantize(Decimal("0.001"))

            cash_advance_fee_amount = min(
                cash_advance_fee_amount,
                available_credit
            ).quantize(Decimal("0.001"))

            if cash_advance_fee_amount > 0:
                transaction = {
                    "transaction_id": f"TR{starting_transaction_counter:06d}",
                    "account_id": account["account_id"],
                    "transaction_timestamp": cash_advance_timestamp,
                    "transaction_type": "Cash Advance Fee",
                    "transaction_direction": "Debit",
                    "amount": cash_advance_fee_amount,
                    "currency": account["currency"],
                    "channel": "System",
                    "merchant_category": None,
                    "created_at": generate_created_at(cash_advance_timestamp),
                }

                card_transactions.append(transaction)
                starting_transaction_counter += 1

                outstanding_balance = (
                    outstanding_balance + cash_advance_fee_amount
                ).quantize(Decimal("0.001"))


        if outstanding_balance > 0 and not is_final_closed_cycle:
            statement_balance = outstanding_balance

            minimum_due = calculate_minimum_card_payment(statement_balance, segment_id)

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

            payment_amount = payment_amount.quantize(Decimal("0.001"))

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
                    schedule_end_date
                )
            else:
                actual_payment_timestamp = due_timestamp

            if should_charge_late_fee:
                late_fee_amount = generate_card_late_fee_amount(segment_id)

                available_credit = (
                    credit_limit - outstanding_balance
                ).quantize(Decimal("0.001"))

                late_fee_amount = min(
                    late_fee_amount,
                    available_credit
                ).quantize(Decimal("0.001"))

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
                    ).quantize(Decimal("0.001"))

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
                ).quantize(Decimal("0.001"))

            if should_charge_interest:
                unpaid_statement_balance = (
                    statement_balance - payment_amount
                ).quantize(Decimal("0.001"))

                interest_amount = calculate_card_interest_charge(
                    unpaid_statement_balance,
                    segment_id
                )

                available_credit = (
                    credit_limit - outstanding_balance
                ).quantize(Decimal("0.001"))

                interest_amount = min(
                    interest_amount,
                    available_credit
                ).quantize(Decimal("0.001"))

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
                    ).quantize(Decimal("0.001"))

        current_cycle_date = cycle_end_date + timedelta(seconds=1)
    
    if account["account_status"] == "Closed" and outstanding_balance > 0:
        settlement_timestamp = account["_activity_end_date"]

        transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": settlement_timestamp,
            "transaction_type": "Card Payment",
            "transaction_direction": "Credit",
            "amount": outstanding_balance.quantize(Decimal("0.001")),
            "currency": account["currency"],
            "channel": choose_channel("Card Payment"),
            "merchant_category": None,
            "created_at": settlement_timestamp,
        }

        card_transactions.append(transaction)
        starting_transaction_counter += 1

        outstanding_balance = Decimal("0.000")

    return card_transactions, starting_transaction_counter

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

def generate_salary_spending_amount(monthly_salary, transaction_type):
    max_ratios = {
        "POS Purchase": Decimal("0.08"),
        "ATM Withdrawal": Decimal("0.15"),
        "Bill Payment": Decimal("0.25"),
        "Transfer Out": Decimal("0.35"),
        "Fee": Decimal("0.01"),
    }

    min_amounts = {
        "POS Purchase": Decimal("2.000"),
        "ATM Withdrawal": Decimal("10.000"),
        "Bill Payment": Decimal("10.000"),
        "Transfer Out": Decimal("10.000"),
        "Fee": Decimal("1.000"),
    }

    min_amount = min_amounts[transaction_type]
    max_amount = monthly_salary * max_ratios[transaction_type]

    if max_amount < min_amount:
        max_amount = min_amount

    amount_in_thousandths = random.randint(
        int(min_amount * 1000),
        int(max_amount * 1000)
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def get_valid_month_day(year, month, preferred_day):
    last_day_of_month = calendar.monthrange(year, month)[1]
    return min(preferred_day, last_day_of_month)

def add_one_month(dt):
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1)

    return dt.replace(month=dt.month + 1)

def generate_salary_account_transactions(account, segment_id, starting_transaction_counter):
    salary_transactions = []

    if segment_id not in SALARY_AMOUNT_RULES:
        raise ValueError(
            f"Salary account generated for invalid segment: {segment_id}"
        )
    
    monthly_salary = choose_monthly_salary(segment_id)
    account["_monthly_salary"] = monthly_salary

    available_balance = generate_opening_balance(segment_id, account["product_id"])

    SALARY_DAY_OPTIONS = [24, 25, 26, 27, 28, 30]

    SALARY_MONTHLY_TRANSACTION_COUNT_RULES = {
        "SEG001": (12, 35),
        "SEG002": (18, 50),
        "SEG005": (20, 70),
    }
    
    schedule_start_date = account["_activity_start_date"]
    schedule_end_date = account["_activity_end_date"]

    salary_day = random.choice(SALARY_DAY_OPTIONS)

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

        if schedule_start_date <= salary_date <= schedule_end_date:
            salary_timestamp = assign_random_business_time(
                salary_date,
                earliest_allowed=schedule_start_date,
                latest_allowed=schedule_end_date
            )

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

            starting_transaction_counter+=1
            salary_transactions.append(transaction)
            running_balance = (
                running_balance + monthly_salary
            ).quantize(Decimal("0.001"))

            monthly_spending_budget = generate_total_salary_spending_amount(
                monthly_salary,
                segment_id
            )

            monthly_spending_budget = min(
                monthly_spending_budget,
                running_balance
            ).quantize(Decimal("0.001"))

            min_count, max_count = SALARY_MONTHLY_TRANSACTION_COUNT_RULES[segment_id]
            transaction_count = random.randint(min_count, max_count)

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
                
            window_ratio = (
                Decimal(actual_window_seconds) / Decimal(full_window_seconds)
            ).quantize(Decimal("0.001"))

            window_ratio = min(window_ratio, Decimal("1.000"))

            full_month_spending_budget = generate_total_salary_spending_amount(
                monthly_salary,
                segment_id
            )

            monthly_spending_budget = (
                full_month_spending_budget * window_ratio
            ).quantize(Decimal("0.001"))

            monthly_spending_budget = min(
                monthly_spending_budget,
                running_balance
            ).quantize(Decimal("0.001"))

            min_count, max_count = SALARY_MONTHLY_TRANSACTION_COUNT_RULES[segment_id]

            base_transaction_count = random.randint(min_count, max_count)

            transaction_count = math.ceil(
                base_transaction_count * float(window_ratio)
            )

            transaction_count = max(1, transaction_count)

            for _ in range(transaction_count):
                if monthly_spending_budget <= 0 or running_balance <= 0:
                    break

                transaction_timestamp = spending_window_start + timedelta(
                    seconds=random.randint(0, actual_window_seconds)
                )

                salary_spending_types_weights = [
                    spending_type["weight"]
                    for spending_type in salary_spending_types
                ]

                transaction_chosen = random.choices(
                    salary_spending_types,
                    weights=salary_spending_types_weights,
                    k=1
                )[0]

                remaining_transactions = transaction_count - _

                average_transaction_amount = (
                    monthly_spending_budget / Decimal(remaining_transactions)
                ).quantize(Decimal("0.001"))

                amount_multiplier = Decimal(str(random.uniform(0.50, 1.75)))

                transaction_amount = (
                    average_transaction_amount * amount_multiplier
                ).quantize(Decimal("0.001"))

                transaction_amount = min(
                    transaction_amount,
                    monthly_spending_budget,
                    running_balance
                ).quantize(Decimal("0.001"))

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
                    "merchant_category": choose_merchant_category(transaction_chosen["transaction_type"]),
                    "created_at": generate_created_at(transaction_timestamp),
                }

                salary_transactions.append(transaction)
                starting_transaction_counter += 1

                running_balance = (
                    running_balance - transaction_amount
                ).quantize(Decimal("0.001"))

                monthly_spending_budget = (
                    monthly_spending_budget - transaction_amount
                ).quantize(Decimal("0.001"))

        current_salary_cycle = add_one_month(current_salary_cycle)
    
    if account["account_status"] == "Closed" and running_balance > 0:
        closure_amount = running_balance.quantize(Decimal("0.001"))

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

    account["current_balance"] = running_balance.quantize(Decimal("0.001"))

    return salary_transactions, starting_transaction_counter

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

def generate_generic_deposit_transactions(account, segment_id, starting_transaction_counter):
    transaction_count = generate_transaction_count(
                segment_id,
                account["product_id"],
                account["account_status"]
            )

    valid_product_transactions = TRANSACTION_RULES_BY_PRODUCT[
                account["product_id"]
    ]

    transaction_type_weights = [
        product_transaction["weight"]
        for product_transaction in valid_product_transactions
    ]

    for _ in range(transaction_count):
        transaction_chosen = random.choices(
            valid_product_transactions,
            weights=transaction_type_weights,
            k=1
        )[0]

    transaction_timestamp = generate_transaction_timestamp(account)
    transaction_counter = starting_transaction_counter

    transaction = {
        "transaction_id": f"TR{transaction_counter:06d}",
        "account_id": account["account_id"],
        "transaction_timestamp": transaction_timestamp,
        "transaction_type": transaction_chosen["transaction_type"],
        "transaction_direction": transaction_chosen["direction"],
        "amount": generate_transaction_amount(
            segment_id,
            account["product_id"],
            transaction_chosen["transaction_type"]
        ),
        "currency": account["currency"],
        "channel": choose_channel(
            transaction_chosen["transaction_type"]
        ),
        "merchant_category": choose_merchant_category(
            transaction_chosen["transaction_type"]
        ),
        "created_at": generate_created_at(transaction_timestamp),
    }

    transactions.append(transaction)
    transaction_counter += 1
    
    return transactions, transaction_counter

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

def generate_core_dataset():
    pass

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

def generate_deposit_transaction_amount(transaction_type, segment_id):
    min_amount, max_amount = DEPOSIT_BASE_AMOUNT_RULES[transaction_type]
    segment_multiplier = SEGMENT_AMOUNT_MULTIPLIER[segment_id]

    base_amount = Decimal(str(
        random.uniform(float(min_amount), float(max_amount))
    ))

    return (
        base_amount * segment_multiplier
    ).quantize(Decimal("0.001"))

def estimate_active_months(start_date, end_date):
    active_seconds = (end_date - start_date).total_seconds()

    if active_seconds <= 0:
        return 0

    seconds_per_month = 30 * 24 * 60 * 60

    return max(
        1,
        math.ceil(active_seconds / seconds_per_month)
    )

def generate_deposit_like_transactions(account, segment_id, starting_transaction_counter):
    deposit_transactions = []

    product_id = account["product_id"]
    account_status = account["account_status"]

    if product_id not in DEPOSIT_LIKE_PRODUCTS:
        raise ValueError(
            f"Invalid deposit-like product passed: {product_id}"
        )

    running_balance = Decimal("0.000")
    opening_balance = account["_opening_balance"].quantize(Decimal("0.001"))

    schedule_start = account["_activity_start_date"]
    schedule_end = account["_activity_end_date"]

    opening_deposit_timestamp = account["created_at"]

    opening_deposit_transaction = {
        "transaction_id": f"TR{starting_transaction_counter:06d}",
        "account_id": account["account_id"],
        "transaction_timestamp": opening_deposit_timestamp,
        "transaction_type": "Opening Deposit",
        "transaction_direction": "Credit",
        "amount": opening_balance,
        "currency": account["currency"],
        "channel": "Branch",
        "merchant_category": None,
        "created_at": generate_created_at(opening_deposit_timestamp),
    }

    deposit_transactions.append(opening_deposit_transaction)
    starting_transaction_counter += 1

    running_balance = opening_balance

    active_months = estimate_active_months(
        schedule_start,
        schedule_end
    )

    min_per_month, max_per_month = DEPOSIT_MONTHLY_TRANSACTION_COUNT_RULES[
        account_status
    ][product_id]

    min_count = min_per_month * active_months
    max_count = max_per_month * active_months

    if max_count <= 0:
        transaction_count = 0
    else:
        transaction_count = random.randint(min_count, max_count)

    random_activity_end = schedule_end

    if account_status == "Closed":
        random_activity_end = schedule_end - timedelta(seconds=1)

    transaction_window_seconds = int(
        (random_activity_end - schedule_start).total_seconds()
    )

    if transaction_window_seconds > 0:
        transaction_timestamps = sorted([
            schedule_start + timedelta(
                seconds=random.randint(0, transaction_window_seconds)
            )
            for _ in range(transaction_count)
        ])
    else:
        transaction_timestamps = []

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

        if transaction_direction == "Debit":
            transaction_amount = min(
                transaction_amount,
                running_balance
            ).quantize(Decimal("0.001"))

            if transaction_amount <= 0:
                continue

            running_balance = (
                running_balance - transaction_amount
            ).quantize(Decimal("0.001"))

        else:
            running_balance = (
                running_balance + transaction_amount
            ).quantize(Decimal("0.001"))

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

    if account_status == "Closed" and running_balance > 0:
        closure_amount = running_balance.quantize(Decimal("0.001"))

        closure_transaction = {
            "transaction_id": f"TR{starting_transaction_counter:06d}",
            "account_id": account["account_id"],
            "transaction_timestamp": schedule_end,
            "transaction_type": "Account Closure Transfer",
            "transaction_direction": "Debit",
            "amount": closure_amount,
            "currency": account["currency"],
            "channel": "System",
            "merchant_category": None,
            "created_at": generate_created_at(schedule_end),
        }

        deposit_transactions.append(closure_transaction)
        starting_transaction_counter += 1

        running_balance = Decimal("0.000")

    account["current_balance"] = running_balance.quantize(Decimal("0.001"))

    return deposit_transactions, starting_transaction_counter

def get_account_created_at(account):
    if "created_at" in account:
        return account["created_at"]

    if "account_created_at" in account:
        return account["account_created_at"]

    raise KeyError(
        "Account is missing created_at/account_created_at. "
        "Opening Deposit audit needs the account creation timestamp."
    )

def audit_deposit_like_accounts(accounts, transactions, max_accounts=10):
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

                if transaction_timestamp == account_created_at:
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

    transactions = generate_transactions(
        accounts,
        crm_dataset["customers"]
    )

    update_accounts_from_transactions(accounts, transactions)

    closed_deposit_accounts = [
        account for account in accounts
        if account["product_id"] in DEPOSIT_LIKE_PRODUCTS
        and account["account_status"] == "Closed"
    ]

    audit_deposit_like_accounts(
        closed_deposit_accounts,
        transactions
    )