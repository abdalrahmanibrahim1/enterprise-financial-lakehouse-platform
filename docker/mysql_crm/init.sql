CREATE TABLE IF NOT EXISTS crm_segments (
    segment_id VARCHAR(20) PRIMARY KEY,
    segment_name VARCHAR(100) NOT NULL,
    risk_band VARCHAR(20) NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS crm_customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    national_id VARCHAR(50),
    full_name VARCHAR(255) NOT NULL,
    birth_date DATE,
    city VARCHAR(100),
    gender VARCHAR(20),
    segment_id VARCHAR(20),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_crm_customers_segment
        FOREIGN KEY (segment_id)
        REFERENCES crm_segments(segment_id)
);

CREATE TABLE IF NOT EXISTS crm_contacts (
    contact_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    contact_type VARCHAR(50) NOT NULL,
    contact_value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_crm_contacts_customer
        FOREIGN KEY (customer_id)
        REFERENCES crm_customers(customer_id)
);

CREATE TABLE IF NOT EXISTS crm_customer_status_history (
    status_history_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_crm_status_history_customer
        FOREIGN KEY (customer_id)
        REFERENCES crm_customers(customer_id)
);

CREATE INDEX idx_crm_customers_updated_at
    ON crm_customers(updated_at);

CREATE INDEX idx_crm_contacts_updated_at
    ON crm_contacts(updated_at);

CREATE INDEX idx_crm_status_history_updated_at
    ON crm_customer_status_history(updated_at);

CREATE INDEX idx_crm_customers_segment_id
    ON crm_customers(segment_id);

CREATE INDEX idx_crm_contacts_customer_id
    ON crm_contacts(customer_id);

CREATE INDEX idx_crm_status_history_customer_id
    ON crm_customer_status_history(customer_id);