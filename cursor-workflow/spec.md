# Project Specification

## Architecture

The solution will use a Databricks Medallion Architecture:

Raw CSV
→ Bronze Delta
→ Silver Delta
→ Gold Delta
→ Databricks SQL Dashboard

---

## Source Datasets

### customers.csv

Expected scale:

Approximately 10,000 records.

The dataset represents customers.

Important fields include:

- customer_id
- customer_name
- email
- customer-related attributes required for segmentation

---

### orders.csv

Expected scale:

Approximately 100,000 records.

The dataset represents customer orders.

Important fields include:

- order_id
- customer_id
- product_id
- order-related measures required for revenue calculations

---

### products.csv

Expected scale:

Approximately 500 records.

The dataset represents products.

Important fields include:

- product_id
- product_name
- category
- product-related attributes required for sales analysis

---

# Bronze Specification

Bronze must:

1. Read the CSV source files.
2. Preserve source records.
3. Store the data in Delta format.
4. Add ingestion metadata.
5. Provide traceability to the source.

Bronze should not remove records simply because they contain data-quality
issues.

---

# Silver Specification

Silver must validate and conform the Bronze data.

## Completeness

Identify missing required values.

Examples:

- customer email
- orders.customer_id
- orders.product_id

## Uniqueness

Identify duplicate identifiers.

Examples:

- customer_id
- order_id

## Referential Integrity

Validate relationships:

orders.customer_id
→ customers.customer_id

orders.product_id
→ products.product_id

## Quality Handling

Bad records should be preserved and identified rather than silently
deleted.

The implementation should provide quality indicators and measurable
quality metrics.

---

# Gold Specification

## Sales by Product

Required analytical output:

- product_id
- product_name
- category
- total_orders
- total_revenue
- average_order_value

## Revenue by Customer

Required analytical output:

- customer_id
- customer_name
- customer_segment
- total_orders
- total_revenue
- average_order_value
- lifetime_value_actual

## Customer Segmentation

Required output:

- customer_segment
- customer_count
- average_revenue
- total_revenue

---

# Dashboard Specification

Required dashboard visualizations:

1. Top 10 Products by Revenue
2. Customer Revenue Distribution
3. Customer Segmentation

---

# Quality Validation

The implementation must demonstrate that intentional data-quality issues
are detected.

The test strategy must cover:

- completeness failures
- uniqueness failures
- referential-integrity failures
- quality metric calculations