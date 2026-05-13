-- Create staging tables from raw CSVs (DuckDB reads CSV directly)
CREATE OR REPLACE TABLE stg_orders AS
SELECT * FROM read_csv_auto($orders_csv, header=true);

CREATE OR REPLACE TABLE stg_order_items AS
SELECT * FROM read_csv_auto($order_items_csv, header=true);

CREATE OR REPLACE TABLE stg_products AS
SELECT * FROM read_csv_auto($products_csv, header=true);

CREATE OR REPLACE TABLE stg_customers AS
SELECT * FROM read_csv_auto($customers_csv, header=true);

CREATE OR REPLACE TABLE stg_order_payments AS
SELECT * FROM read_csv_auto($payments_csv, header=true);
