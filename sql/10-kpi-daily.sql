-- KPI mart: daily KPIs + segmentation columns needed for root cause

CREATE OR REPLACE VIEW mart_order_facts AS
WITH base AS (
  SELECT
    o.order_id,
    CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_ts,
    CAST(o.order_purchase_timestamp AS DATE) AS purchase_date,
    o.order_status,
    c.customer_state,
    oi.product_id,
    oi.price,
    oi.freight_value
  FROM stg_orders o
  JOIN stg_customers c ON c.customer_id = o.customer_id
  JOIN stg_order_items oi ON oi.order_id = o.order_id
),
with_products AS (
  SELECT
    b.*,
    p.product_category_name
  FROM base b
  LEFT JOIN stg_products p ON p.product_id = b.product_id
),
with_payments AS (
  SELECT
    wp.*,
    pay.payment_type,
    pay.payment_value
  FROM with_products wp
  LEFT JOIN stg_order_payments pay ON pay.order_id = wp.order_id
)
SELECT * FROM with_payments;

CREATE OR REPLACE VIEW kpi_daily AS
WITH daily AS (
  SELECT
    purchase_date AS ds,

    -- KPI 1: revenue = sum(price + freight) for delivered orders
    SUM(
      CASE WHEN order_status = 'delivered' THEN (price + freight_value) ELSE 0 END
    ) AS revenue,

    -- KPI 2: orders = distinct delivered orders
    COUNT(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id ELSE NULL END) AS orders,

    -- KPI 3: AOV = revenue / orders
    CASE
      WHEN COUNT(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id ELSE NULL END) = 0 THEN NULL
      ELSE
        SUM(CASE WHEN order_status = 'delivered' THEN (price + freight_value) ELSE 0 END)
        / COUNT(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id ELSE NULL END)
    END AS aov,

    -- KPI 4: payment_fail_rate (proxy governance signal)
    -- treat non-delivered as "failed/aborted" from an operational lens
    CASE
      WHEN COUNT(DISTINCT order_id) = 0 THEN NULL
      ELSE
        1.0 * COUNT(DISTINCT CASE WHEN order_status <> 'delivered' THEN order_id ELSE NULL END)
        / COUNT(DISTINCT order_id)
    END AS payment_fail_rate
  FROM mart_order_facts
  GROUP BY 1
)
SELECT * FROM daily
ORDER BY ds;
