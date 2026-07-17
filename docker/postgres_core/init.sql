CREATE TABLE IF NOT EXISTS core_branches (
    branch_id VARCHAR(20) PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS core_products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    product_type VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS core_accounts (
    account_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    branch_id VARCHAR(20),
    product_id VARCHAR(20),
    account_open_date DATE NOT NULL,
    account_status VARCHAR(50) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    current_balance DECIMAL(18, 3) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_core_accounts_branch
        FOREIGN KEY (branch_id)
        REFERENCES core_branches(branch_id),

    CONSTRAINT fk_core_accounts_product
        FOREIGN KEY (product_id)
        REFERENCES core_products(product_id)
);

CREATE TABLE IF NOT EXISTS core_transactions (
    transaction_id VARCHAR(30) PRIMARY KEY,
    account_id VARCHAR(20) NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    transaction_direction VARCHAR(10) NOT NULL,
    amount DECIMAL(18, 3) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    merchant_category VARCHAR(100),
    created_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_core_transactions_account
        FOREIGN KEY (account_id)
        REFERENCES core_accounts(account_id)
);

CREATE INDEX idx_core_accounts_customer_id
    ON core_accounts(customer_id);

CREATE INDEX idx_core_accounts_updated_at
    ON core_accounts(updated_at);

CREATE INDEX idx_core_transactions_account_id
    ON core_transactions(account_id);

CREATE INDEX idx_core_transactions_created_at
    ON core_transactions(created_at);

CREATE INDEX idx_core_transactions_timestamp
    ON core_transactions(transaction_timestamp);