CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    industry      TEXT,
    sales_rep     TEXT,
    email         TEXT,
    status        TEXT,
    updated_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id      TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id),
    amount          NUMERIC(14,2) NOT NULL,
    invoice_date    DATE NOT NULL,
    due_date        DATE NOT NULL,
    payment_status  TEXT NOT NULL,
    updated_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id       BIGSERIAL PRIMARY KEY,
    customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
    sale_date     DATE NOT NULL,
    product       TEXT NOT NULL,
    quantity      NUMERIC(12,2) NOT NULL,
    unit_price    NUMERIC(14,2) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_sale_natural_key UNIQUE (customer_id, sale_date, product, quantity, unit_price)
);

CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_sale_date ON sales(sale_date);