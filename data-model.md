# Data Model — Databricks Medallion Pipeline

**Phase:** 4 — Solution Design  
**Status:** Approved design baseline  
**Related:** `design-notes.md`, `data-quality-strategy.md`

---

## 1. Overview

This document defines source CSV schemas, layer-to-layer mappings, and target table structures for Bronze, Silver, Gold, and DQ layers.

**Naming convention:** `{layer}_{entity}` tables in configurable schemas under catalog `medallion_eval` (default).

---

## 2. Source CSV Datasets

### 2.1 File locations

| File | Path | Git policy |
|---|---|---|
| `customers.csv` | `data/raw/customers.csv` | Gitignored |
| `orders.csv` | `data/raw/orders.csv` | Gitignored |
| `products.csv` | `data/raw/products.csv` | Gitignored |

### 2.2 Row counts

| Dataset | Base rows (clean generation) | Final rows (after DQ injection) | Notes |
|---|---|---|---|
| customers | 10,000 | 10,015 | +15 duplicate-injected rows (15 duplicate `customer_id` pairs) |
| orders | 100,000 | 100,035 | +35 duplicate-injected rows (approved; see DQ strategy) |
| products | 500 | 500 | No row-count injection |

**Important:** Base counts are the clean generation targets. Final counts reflect appended duplicate rows for uniqueness testing. Bronze row counts must match final CSV row counts exactly.

---

## 3. Source Schemas

### 3.1 `customers.csv`

| Column | Type | Required | Description |
|---|---|---|---|
| `customer_id` | string | yes | Primary business key |
| `customer_name` | string | yes | Customer display name |
| `email` | string | yes | Email address; completeness DQ target |
| `registration_date` | date | no | Customer registration date |
| `country` | string | no | Customer country |
| `signup_channel` | string | no | Acquisition channel (web, mobile, referral, etc.); contextual attribute for segmentation documentation |

### 3.2 `orders.csv`

| Column | Type | Required | Description |
|---|---|---|---|
| `order_id` | string | yes | Primary business key |
| `customer_id` | string | yes | FK to customers; completeness + RI DQ target |
| `product_id` | string | yes | FK to products; completeness + RI DQ target |
| `order_date` | date | yes | Order date |
| `quantity` | integer | yes | Units ordered |
| `unit_price` | decimal(10,2) | yes | Price per unit at time of order |

### 3.3 `products.csv`

| Column | Type | Required | Description |
|---|---|---|---|
| `product_id` | string | yes | Primary business key |
| `product_name` | string | yes | Product display name |
| `category` | string | yes | Product category |
| `list_price` | decimal(10,2) | no | Catalog list price |
| `is_active` | boolean | no | Whether product is active |

### 3.4 ID formats (generation convention)

| Entity | Format | Example |
|---|---|---|
| Customer | `CUST-{5-digit}` | `CUST-00001` |
| Order | `ORD-{7-digit}` | `ORD-0000001` |
| Product | `PROD-{3-digit}` | `PROD-001` |

---

## 4. Entity Relationships

```
customers (1) ──< orders (many) >── (1) products
```

| Relationship | From | To | Rule |
|---|---|---|---|
| Order → Customer | `orders.customer_id` | `customers.customer_id` | RI check in Silver |
| Order → Product | `orders.product_id` | `products.product_id` | RI check in Silver |

---

## 5. Revenue Model

| Field / Metric | Level | Formula | Computed in |
|---|---|---|---|
| `line_revenue` | Order | `quantity * unit_price` | Silver |
| `total_revenue` | Customer / Product | `SUM(line_revenue)` over **valid orders** | Gold |
| `total_orders` | Customer / Product | `COUNT(DISTINCT order_id)` over **valid orders** | Gold |
| `average_order_value` | Customer / Product | `total_revenue / total_orders` (null if 0 orders) | Gold |
| `lifetime_value_actual` | Customer | **Equal to `total_revenue`** | Gold |

**Currency:** USD implied; single currency, no FX conversion.

**Gold input filter:** Only orders where `silver_orders.is_valid_record = true` contribute to revenue metrics. Invalid orders remain in Silver.

---

## 6. Customer Segmentation Model

Segmentation is derived at Gold build time from each customer's `total_revenue` (valid orders only):

| `customer_segment` | Condition on `total_revenue` |
|---|---|
| No Purchase | = 0 |
| Low Value | > 0 and < 500 |
| Mid Value | >= 500 and < 2000 |
| High Value | >= 2000 |

`signup_channel` is stored on the customer record for analytical context but does **not** drive the segment assignment. Segmentation is deterministic, revenue-based, and contains no machine learning.

---

## 7. Bronze Layer Tables

### 7.1 Design principles

- Preserve all source business columns as ingested (string-preserving read recommended).
- Add ingestion metadata columns.
- No cleaning, deduplication, type repair, or row removal.

### 7.2 `bronze_customers`

| Column | Source | Notes |
|---|---|---|
| `customer_id` | CSV | Raw value |
| `customer_name` | CSV | Raw value |
| `email` | CSV | Raw value |
| `registration_date` | CSV | Raw value |
| `country` | CSV | Raw value |
| `signup_channel` | CSV | Raw value |
| `_ingest_batch_id` | Metadata | Pipeline run identifier |
| `_ingest_timestamp` | Metadata | UTC ingest timestamp |
| `_source_file` | Metadata | e.g. `customers.csv` |
| `_source_row_number` | Metadata | 1-based row number in source file |
| `_bronze_record_id` | Metadata | Surrogate: `_source_file` + `_source_row_number` |

### 7.3 `bronze_orders`

| Column | Source |
|---|---|
| `order_id` | CSV |
| `customer_id` | CSV |
| `product_id` | CSV |
| `order_date` | CSV |
| `quantity` | CSV |
| `unit_price` | CSV |
| `_ingest_batch_id` | Metadata |
| `_ingest_timestamp` | Metadata |
| `_source_file` | Metadata |
| `_source_row_number` | Metadata |
| `_bronze_record_id` | Metadata |

### 7.4 `bronze_products`

| Column | Source |
|---|---|
| `product_id` | CSV |
| `product_name` | CSV |
| `category` | CSV |
| `list_price` | CSV |
| `is_active` | CSV |
| `_ingest_batch_id` | Metadata |
| `_ingest_timestamp` | Metadata |
| `_source_file` | Metadata |
| `_source_row_number` | Metadata |
| `_bronze_record_id` | Metadata |

---

## 8. Silver Layer Tables

### 8.1 Conformance transformations

Applied in Silver (not Bronze):

| Transformation | Applies to |
|---|---|
| Trim string whitespace | All string business columns |
| Cast `quantity` to integer | orders |
| Cast `unit_price`, `list_price` to decimal(10,2) | orders, products |
| Cast `registration_date`, `order_date` to date | customers, orders |
| Cast `is_active` to boolean | products |
| Compute `line_revenue` | orders |

### 8.2 `silver_customers`

Includes all Bronze customer columns (conformed) plus:

| Column | Type | Description |
|---|---|---|
| `is_email_complete` | boolean | `true` if email is not null and not blank after trim |
| `is_customer_id_unique` | boolean | `true` if `customer_id` appears exactly once in Silver customers |
| `is_valid_record` | boolean | `is_email_complete AND is_customer_id_unique` |
| `dq_failure_reasons` | array\<string\> | Optional diagnostic list of failed rule codes |

**Row count:** Equal to `bronze_customers`.

### 8.3 `silver_orders`

Includes all Bronze order columns (conformed) plus:

| Column | Type | Description |
|---|---|---|
| `line_revenue` | decimal(10,2) | `quantity * unit_price` |
| `is_customer_id_complete` | boolean | `customer_id` not null/blank |
| `is_product_id_complete` | boolean | `product_id` not null/blank |
| `is_order_id_unique` | boolean | `order_id` appears exactly once in Silver orders |
| `is_customer_id_valid_ref` | boolean | `customer_id` exists in `silver_customers.customer_id` |
| `is_product_id_valid_ref` | boolean | `product_id` exists in `silver_products.product_id` |
| `is_valid_record` | boolean | All five order-level flags are `true` |
| `dq_failure_reasons` | array\<string\> | Optional diagnostic list of failed rule codes |

**Row count:** Equal to `bronze_orders`.

**RI note:** FK existence is checked against the corresponding Silver entity table (all IDs present in that table), regardless of whether the referenced customer row is itself fully valid.

### 8.4 `silver_products`

Includes all Bronze product columns (conformed) plus:

| Column | Type | Description |
|---|---|---|
| `is_valid_record` | boolean | Always `true` (no required DQ rules on products) |

**Row count:** Equal to `bronze_products`.

---

## 9. Gold Layer Tables

### 9.1 `gold_sales_by_product`

| Column | Type | Source / logic |
|---|---|---|
| `product_id` | string | `silver_products.product_id` |
| `product_name` | string | `silver_products.product_name` |
| `category` | string | `silver_products.category` |
| `total_orders` | long | `COUNT(DISTINCT order_id)` from valid `silver_orders` |
| `total_revenue` | decimal(12,2) | `SUM(line_revenue)` from valid `silver_orders` |
| `average_order_value` | decimal(12,2) | `total_revenue / total_orders`; null if 0 |

**Grain:** One row per product with at least one valid order (products with zero valid orders may be omitted or included with zeros — implementation should document choice; recommend include all active products with zero defaults).

### 9.2 `gold_revenue_by_customer`

| Column | Type | Source / logic |
|---|---|---|
| `customer_id` | string | `silver_customers.customer_id` where `is_valid_record = true` |
| `customer_name` | string | `silver_customers.customer_name` |
| `customer_segment` | string | Derived from `total_revenue` per segmentation model |
| `total_orders` | long | Valid orders per customer |
| `total_revenue` | decimal(12,2) | Sum of `line_revenue` for valid orders |
| `average_order_value` | decimal(12,2) | `total_revenue / total_orders` |
| `lifetime_value_actual` | decimal(12,2) | **Equal to `total_revenue`** |

**Grain:** One row per valid customer record.

### 9.3 `gold_customer_segmentation`

| Column | Type | Source / logic |
|---|---|---|
| `customer_segment` | string | Segment label |
| `customer_count` | long | Distinct valid customers in segment |
| `average_revenue` | decimal(12,2) | `AVG(total_revenue)` across customers in segment |
| `total_revenue` | decimal(12,2) | `SUM(total_revenue)` across customers in segment |

**Grain:** One row per segment (four segments expected).

---

## 10. DQ Metrics Tables

### 10.1 `dq_metrics`

| Column | Type | Description |
|---|---|---|
| `metric_run_id` | string | Pipeline run identifier |
| `metric_timestamp` | timestamp | UTC metric capture time |
| `dataset` | string | `customers`, `orders`, or `products` |
| `total_records` | long | Total Silver rows |
| `valid_records` | long | Rows where `is_valid_record = true` |
| `invalid_records` | long | Rows where `is_valid_record = false` |
| `valid_record_pct` | double | `valid_records / total_records` |

### 10.2 `dq_metrics_by_rule`

| Column | Type | Description |
|---|---|---|
| `metric_run_id` | string | Pipeline run identifier |
| `dataset` | string | Entity name |
| `rule_code` | string | Stable issue code (see DQ strategy) |
| `rule_category` | string | completeness / uniqueness / referential_integrity |
| `failed_record_count` | long | Rows failing the rule |
| `expected_failed_count` | long | Expected count from injection manifest |

---

## 11. Source-to-Target Mapping Summary

| Source | Bronze | Silver | Gold |
|---|---|---|---|
| `customers.csv` | `bronze_customers` | `silver_customers` | `gold_revenue_by_customer`, `gold_customer_segmentation` |
| `orders.csv` | `bronze_orders` | `silver_orders` | `gold_sales_by_product`, `gold_revenue_by_customer` |
| `products.csv` | `bronze_products` | `silver_products` | `gold_sales_by_product` |

---

## 12. Dashboard Data Mapping

| Dashboard visualization | Primary Gold table | Key columns |
|---|---|---|
| Top 10 Products by Revenue | `gold_sales_by_product` | `product_name`, `total_revenue` |
| Customer Revenue Distribution | `gold_revenue_by_customer` | `total_revenue` |
| Customer Segmentation | `gold_customer_segmentation` | `customer_segment`, `customer_count`, `total_revenue`, `average_revenue` |
