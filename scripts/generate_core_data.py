import random
from datetime import datetime, timedelta
from decimal import Decimal

ACCOUNT_COUNT_RULES = {
        # Retail customers: usually 1 account, sometimes 2, rarely 3
        "SEG001" : {
            "options" : [1, 2, 3],
            "weights" : [75, 22, 3],
        },

        # Premium customers: more likely to have multiple accounts
        "SEG002" : {
            "options" : [1, 2, 3],
            "weights" : [50, 35, 15],
        },
        
        # SME customers : often business + another account
        "SEG003" : {
            "options" : [1, 2, 3],
            "weights" : [40, 45, 15]
        },

        # Corporate customers: usually multiple accounts
        "SEG004" : {
            "options" : [1, 2, 3],
            "weights" : [20, 45, 35]
        },

        # Private banking customers: often multiple accounts/products
        "SEG005": {
            "options": [1, 2, 3],
            "weights": [35, 40, 25],
        },
    }

PRODUCT_WEIGHTS_BY_SEGMENT = {
        # Retail: normal individual customers
        "SEG001": {
            "PRD001": 30,  # Current Account
            "PRD002": 30,  # Savings Account
            "PRD003": 25,  # Salary Account
            "PRD004": 1,   # Business Account - rare/misclassified/sole proprietor
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
        "SEG001": {
            "PRD001": [0, 7_500],
            "PRD002": [0, 20_000],
            "PRD003": [0, 5_000],
            "PRD004": [0, 25_000],
            "PRD005": [-25_000, -1_000],
            "PRD006": [-45_000, -5_000],
            "PRD007": [-3_000, 0],
            "PRD008": [-120_000, -20_000],
        },
        "SEG002": {
            "PRD001": [500, 25_000],
            "PRD002": [5_000, 100_000],
            "PRD003": [1_000, 10_000],
            "PRD004": [5_000, 75_000],
            "PRD005": [-60_000, -5_000],
            "PRD006": [-70_000, -10_000],
            "PRD007": [-10_000, 0],
            "PRD008": [-250_000, -50_000],
        },
        "SEG003": {
            "PRD001": [1_000, 75_000],
            "PRD002": [0, 50_000],
            "PRD003": [],
            "PRD004": [5_000, 250_000],
            "PRD005": [],
            "PRD006": [-100_000, -10_000],
            "PRD007": [-25_000, 0],
            "PRD008": [-500_000, -50_000],
        },
        "SEG004": {
            "PRD001": [10_000, 500_000],
            "PRD002": [0, 250_000],
            "PRD003": [],
            "PRD004": [50_000, 2_000_000],
            "PRD005": [],
            "PRD006": [-500_000, -50_000],
            "PRD007": [-100_000, 0],
            "PRD008": [-5_000_000, -250_000],
        },
        "SEG005": {
            "PRD001": [10_000, 150_000],
            "PRD002": [25_000, 750_000],
            "PRD003": [5_000, 20_000],
            "PRD004": [10_000, 250_000],
            "PRD005": [-100_000, -10_000],
            "PRD006": [-200_000, -30_000],
            "PRD007": [-50_000, 0],
            "PRD008": [-2_000_000, -100_000],
        },
    }

MAX_UPDATE_DATE = datetime(2026, 6, 30)

TRANSACTION_RULES_BY_PRODUCT = {
    # PRD001 - Current Account
    "PRD001": [
        {"transaction_type": "Cash Deposit", "direction": "Credit", "weight": 12},
        {"transaction_type": "Transfer In", "direction": "Credit", "weight": 18},
        {"transaction_type": "ATM Withdrawal", "direction": "Debit", "weight": 18},
        {"transaction_type": "POS Purchase", "direction": "Debit", "weight": 17},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 17},
        {"transaction_type": "Bill Payment", "direction": "Debit", "weight": 12},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 6},
    ],

    # PRD002 - Savings Account
    "PRD002": [
        {"transaction_type": "Deposit", "direction": "Credit", "weight": 20},
        {"transaction_type": "Transfer In", "direction": "Credit", "weight": 25},
        {"transaction_type": "Interest Credit", "direction": "Credit", "weight": 10},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 25},
        {"transaction_type": "Withdrawal", "direction": "Debit", "weight": 15},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 5},
    ],

    # PRD003 - Salary Account
    "PRD003": [
        {"transaction_type": "Salary Credit", "direction": "Credit", "weight": 15},
        {"transaction_type": "ATM Withdrawal", "direction": "Debit", "weight": 25},
        {"transaction_type": "POS Purchase", "direction": "Debit", "weight": 25},
        {"transaction_type": "Bill Payment", "direction": "Debit", "weight": 15},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 15},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 5},
    ],

    # PRD004 - Business Account
    "PRD004": [
        {"transaction_type": "Customer Payment", "direction": "Credit", "weight": 25},
        {"transaction_type": "POS Settlement", "direction": "Credit", "weight": 15},
        {"transaction_type": "Cash Deposit", "direction": "Credit", "weight": 10},
        {"transaction_type": "Transfer In", "direction": "Credit", "weight": 10},
        {"transaction_type": "Supplier Payment", "direction": "Debit", "weight": 20},
        {"transaction_type": "Payroll Payment", "direction": "Debit", "weight": 10},
        {"transaction_type": "Transfer Out", "direction": "Debit", "weight": 7},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 3},
    ],

    # PRD005 - Personal Loan
    "PRD005": [
        {"transaction_type": "Loan Disbursement", "direction": "Debit", "weight": 3},
        {"transaction_type": "Loan Repayment", "direction": "Credit", "weight": 77},
        {"transaction_type": "Interest Charge", "direction": "Debit", "weight": 15},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 5},
    ],

    # PRD006 - Auto Loan
    "PRD006": [
        {"transaction_type": "Loan Disbursement", "direction": "Debit", "weight": 3},
        {"transaction_type": "Loan Repayment", "direction": "Credit", "weight": 77},
        {"transaction_type": "Interest Charge", "direction": "Debit", "weight": 15},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 5},
    ],

    # PRD007 - Credit Card
    "PRD007": [
        {"transaction_type": "Card Purchase", "direction": "Debit", "weight": 52},
        {"transaction_type": "Card Payment", "direction": "Credit", "weight": 20},
        {"transaction_type": "Refund", "direction": "Credit", "weight": 5},
        {"transaction_type": "Cash Advance", "direction": "Debit", "weight": 5},
        {"transaction_type": "Interest Charge", "direction": "Debit", "weight": 10},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 4},
        {"transaction_type": "Late Fee", "direction": "Debit", "weight": 4},
    ],

    # PRD008 - Mortgage
    "PRD008": [
        {"transaction_type": "Loan Disbursement", "direction": "Debit", "weight": 2},
        {"transaction_type": "Loan Repayment", "direction": "Credit", "weight": 78},
        {"transaction_type": "Interest Charge", "direction": "Debit", "weight": 18},
        {"transaction_type": "Fee", "direction": "Debit", "weight": 2},
    ],
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

    "Customer Payment": [
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
        {"channel": "Branch", "weight": 70},
        {"channel": "ATM", "weight": 20},
        {"channel": "Mobile", "weight": 10},
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
        {"channel": "POS", "weight": 70},
        {"channel": "System", "weight": 30},
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
        {"channel": "System", "weight": 5},
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

TRANSACTION_AMOUNT_RULES = {
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
        "Salary Credit": [400, 2_500],
        "Loan Disbursement": [1_000, 25_000],
        "Loan Repayment": [50, 800],
        "Interest Charge": [10, 500],
        "Card Purchase": [2, 300],
        "Card Payment": [20, 1_000],
        "Refund": [2, 300],
        "Cash Advance": [20, 500],
        "Late Fee": [5, 50],
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
        "Salary Credit": [1_000, 7_000],
        "Loan Disbursement": [5_000, 60_000],
        "Loan Repayment": [150, 2_000],
        "Interest Charge": [25, 1_000],
        "Card Purchase": [5, 1_500],
        "Card Payment": [100, 5_000],
        "Refund": [5, 1_500],
        "Cash Advance": [50, 2_000],
        "Late Fee": [10, 100],
        "Customer Payment": [100, 25_000],
        "POS Settlement": [100, 30_000],
        "Supplier Payment": [100, 30_000],
        "Payroll Payment": [1_000, 50_000],
    },

    "SEG003": {
        "Cash Deposit": [100, 25_000],
        "Transfer In": [100, 50_000],
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
        "Loan Disbursement": [10_000, 100_000],
        "Loan Repayment": [300, 5_000],
        "Interest Charge": [50, 2_000],
        "Card Purchase": [10, 3_000],
        "Card Payment": [100, 10_000],
        "Refund": [10, 3_000],
        "Cash Advance": [100, 5_000],
        "Late Fee": [20, 200],
        "ATM Withdrawal": [20, 1_000],
        "POS Purchase": [5, 1_000],
    },

    "SEG004": {
        "Cash Deposit": [1_000, 100_000],
        "Transfer In": [1_000, 500_000],
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
        "Loan Disbursement": [50_000, 1_000_000],
        "Loan Repayment": [2_000, 50_000],
        "Interest Charge": [500, 25_000],
        "Card Purchase": [100, 20_000],
        "Card Payment": [1_000, 100_000],
        "Refund": [100, 20_000],
        "Cash Advance": [500, 50_000],
        "Late Fee": [50, 1_000],
        "ATM Withdrawal": [100, 5_000],
        "POS Purchase": [50, 10_000],
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
        "Salary Credit": [5_000, 20_000],
        "Customer Payment": [1_000, 100_000],
        "POS Settlement": [1_000, 100_000],
        "Supplier Payment": [1_000, 150_000],
        "Payroll Payment": [5_000, 150_000],
        "Loan Disbursement": [10_000, 500_000],
        "Loan Repayment": [500, 15_000],
        "Interest Charge": [100, 10_000],
        "Card Purchase": [20, 10_000],
        "Card Payment": [500, 50_000],
        "Refund": [20, 10_000],
        "Cash Advance": [500, 20_000],
        "Late Fee": [20, 500],
    },
}

def generate_branches():
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
    rule = ACCOUNT_COUNT_RULES[segment_id]

    return random.choices(
        rule["options"],
        weights = rule["weights"],
        k = 1
    )[0]

def choose_product_id(segment_id, available_product_ids):
    weights = [
        PRODUCT_WEIGHTS_BY_SEGMENT[segment_id][product_id]
        for product_id in available_product_ids
    ]

    return random.choices(
        available_product_ids,
        weights = weights,
        k = 1
    )[0]

def choose_branch_id(customer_city, branches):
    same_city_branches = [
        branch for branch in branches
        if branch["city"] == customer_city
    ]

    # Most customers use a branch in their own city if one exists.
    if same_city_branches and random.random() < 0.85:
        return random.choice(same_city_branches)["branch_id"]
    
    branch_ids = [branch["branch_id"] for branch in branches]

    branch_weights = [
        BRANCH_WEIGHTS_BY_ID[branch_id]
        for branch_id in branch_ids
    ]

    return random.choices(
        branch_ids,
        weights= branch_weights,
        k = 1
    )[0]

def choose_currency(segment_id):
    rule = CURRENCY_RULES[segment_id]

    return random.choices(
        rule["currencies"],
        weights=rule["weights"],
        k=1
    )[0]

def generate_balance(account_status, segment_id, product_id):
    limits = BALANCE_LIMIT_RULES[segment_id][product_id]

    if not limits:
        raise ValueError(
            f"Invalid product {product_id} for segment {segment_id}"
        )

    if account_status == "Closed":
        return Decimal("0.000")

    min_amount, max_amount = limits

    amount_in_thousandths = random.randint(
        min_amount * 1000,
        max_amount * 1000
    )

    return (Decimal(amount_in_thousandths) / Decimal("1000")).quantize(
        Decimal("0.001")
    )

def generate_accounts(customers, branches, products):
    accounts = []
    account_counter = 1

    for customer in customers:
        customer_id = customer["customer_id"]
        customer_city = customer["city"]
        segment_id = customer["segment_id"]
        customer_created_at = customer["created_at"]

        number_of_accounts = choose_account_count(segment_id)

        available_product_ids = [
            product["product_id"]
            for product in products
        ]

        for _ in range(number_of_accounts):
            product_id = choose_product_id(segment_id, available_product_ids)
            available_product_ids.remove(product_id)

            branch_id = choose_branch_id(customer_city, branches)

            days_after_customer_creation = (
                MAX_UPDATE_DATE - customer_created_at
            ).days

            account_created_at = customer_created_at + timedelta(
                days=random.randint(0, days_after_customer_creation)
            )

            account_status = random.choices(
                ["Active", "Dormant", "Closed", "Frozen"],
                weights=[85, 8, 5, 2],
                k=1
            )[0]

            days_after_account_creation = (
                MAX_UPDATE_DATE - account_created_at
            ).days

            account_updated_at = account_created_at + timedelta(
                days=random.randint(0, days_after_account_creation)
            )

            account = {
                "account_id": f"ACC{account_counter:06d}",
                "customer_id": customer_id,
                "branch_id": branch_id,
                "product_id": product_id,
                "account_open_date": account_created_at.date(),
                "account_status": account_status,
                "currency": choose_currency(segment_id),
                "current_balance": generate_balance(account_status, segment_id, product_id),
                "created_at": account_created_at,
                "updated_at": account_updated_at,
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
    min_datetime = account["created_at"]
    max_datetime = MAX_UPDATE_DATE.replace(hour=23, minute=59, second=59)

    total_seconds = int((max_datetime - min_datetime).total_seconds())

    if total_seconds <= 0:
        return min_datetime

    return min_datetime + timedelta(
        seconds=random.randint(0, total_seconds)
    )

def generate_created_at(transaction_timestamp):
    return transaction_timestamp + timedelta(
        minutes=random.randint(0, 10),
        seconds=random.randint(0, 59),
    )

def generate_transaction_amount(segment_id, product_id, transaction_type):
    segment_rules = TRANSACTION_AMOUNT_RULES.get(segment_id)

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

def generate_transactions(accounts, customers):
    customer_segment_by_id = {
        customer["customer_id"]: customer["segment_id"]
        for customer in customers
    }

    transactions = []
    transaction_counter = 1

    for account in accounts:
        transaction_count = random.randint(1, 10)

        valid_product_transactions = TRANSACTION_RULES_BY_PRODUCT[account["product_id"]]
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

            merchant_category = choose_merchant_category(transaction_chosen["transaction_type"])

            channel = choose_channel(
                transaction_chosen["transaction_type"]
            )

            transaction_timestamp = generate_transaction_timestamp(account)
            created_at = generate_created_at(transaction_timestamp)
            
            segment_id = customer_segment_by_id[account["customer_id"]]

            amount = generate_transaction_amount(
                segment_id,
                account["product_id"],
                transaction_chosen["transaction_type"]
            )

            transaction = {
                "transaction_id": f"TR{transaction_counter:06d}",
                "account_id": account["account_id"],
                "transaction_timestamp": transaction_timestamp,
                "transaction_type": transaction_chosen["transaction_type"],
                "transaction_direction": transaction_chosen["direction"],
                "amount": amount,
                "currency": account["currency"],
                "channel": channel,
                "merchant_category": merchant_category,
                "created_at": created_at,
            }

            transactions.append(transaction)
            transaction_counter += 1

    return transactions

def generate_core_dataset():
    pass

if __name__ == "__main__":
    from collections import Counter
    from pprint import pprint

    from scripts.generate_crm_data import generate_crm_dataset

    branches = generate_branches()
    products = generate_products()

    crm_dataset = generate_crm_dataset(1000)
    accounts = generate_accounts(
        crm_dataset["customers"],
        branches,
        products
    )

    print(f"Branches generated: {len(branches)}")
    print(f"Products generated: {len(products)}")
    print(f"Customers used: {len(crm_dataset['customers'])}")
    print(f"Accounts generated: {len(accounts)}")

    print("\nAccount status distribution:")
    pprint(Counter(account["account_status"] for account in accounts))

    print("\nCurrency distribution:")
    pprint(Counter(account["currency"] for account in accounts))

    print("\nProduct distribution:")
    pprint(Counter(account["product_id"] for account in accounts))

    print("\nBranch distribution:")
    pprint(Counter(account["branch_id"] for account in accounts))

    print("\nSample accounts:")
    pprint(accounts[:10])

    transactions = generate_transactions(accounts, crm_dataset["customers"])

    print(f"Transactions generated: {len(transactions)}")

    print("\nTransaction type distribution:")
    pprint(Counter(transaction["transaction_type"] for transaction in transactions))

    print("\nTransaction direction distribution:")
    pprint(Counter(transaction["transaction_direction"] for transaction in transactions))

    print("\nChannel distribution:")
    pprint(Counter(transaction["channel"] for transaction in transactions))

    print("\nMerchant category distribution:")
    pprint(Counter(transaction["merchant_category"] for transaction in transactions))

    print("\nSample transactions:")
    pprint(transactions[:10])