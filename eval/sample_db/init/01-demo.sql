-- Tiny demo dataset. Postgres runs this ONLY when the sampledata volume is first created.
-- The full evaluation dataset arrives in Iteration 13.

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id            SERIAL PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers (id),
    status        TEXT NOT NULL CHECK (status IN ('completed', 'cancelled', 'pending')),
    total_amount  NUMERIC(12, 2) NOT NULL,
    ordered_at    TIMESTAMPTZ NOT NULL
);

COMMENT ON TABLE customers IS 'People who have placed, or could place, orders.';
COMMENT ON COLUMN orders.total_amount IS 'Order total before any refunds.';

INSERT INTO customers (full_name, email, created_at) VALUES
    ('Asha Rao',     'asha@example.com',   '2025-04-02 10:00+00'),
    ('Rohan Mehta',  'rohan@example.com',  '2025-05-14 09:30+00'),
    ('Priya Nair',   'priya@example.com',  '2025-07-21 16:45+00'),
    ('Vikram Shah',  'vikram@example.com', '2025-09-03 12:10+00'),
    ('Neha Kulkarni','neha@example.com',   '2025-11-18 08:20+00');

INSERT INTO orders (customer_id, status, total_amount, ordered_at) VALUES
    (1, 'completed', 1250.00, '2025-05-01 11:00+00'),
    (1, 'completed',  830.50, '2025-08-12 14:20+00'),
    (2, 'completed', 2100.00, '2025-06-09 10:05+00'),
    (2, 'cancelled',  450.00, '2025-10-02 17:40+00'),
    (3, 'completed',  990.00, '2025-09-15 13:15+00'),
    (4, 'pending',    310.75, '2026-01-20 09:00+00'),
    (5, 'completed', 1760.25, '2026-02-11 15:30+00'),
    (3, 'completed',  540.00, '2026-03-05 12:00+00');

-- Least-privilege role for QueryWise. Dev-only password.
CREATE ROLE qw_readonly LOGIN PASSWORD 'readonly_dev_pw';
GRANT CONNECT ON DATABASE sample TO qw_readonly;
GRANT USAGE ON SCHEMA public TO qw_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO qw_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO qw_readonly;