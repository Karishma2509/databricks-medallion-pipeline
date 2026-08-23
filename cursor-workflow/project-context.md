# Project Context

## Project Name

Databricks Medallion Pipeline — GenAI Coding Evaluation

## Project Objective

Build an end-to-end e-commerce sales data pipeline using Databricks
Medallion Architecture.

The pipeline will process three CSV datasets:

- customers.csv
- orders.csv
- products.csv

The target architecture is:

CSV Source
→ Bronze
→ Silver
→ Gold
→ Databricks SQL Dashboard

## Expected Source Data

The project requires approximately:

- 10,000 customers
- 100,000 orders
- 500 products

The data generator must intentionally introduce approximately 700
problematic records so that the Silver layer can identify them.

## Bronze Layer

The Bronze layer must:

- ingest the raw CSV files
- preserve the source data
- store the data in Delta format
- add ingestion metadata
- support traceability of source records

Bronze should not silently clean or remove source-quality issues.

## Silver Layer

The Silver layer is responsible for:

- data-quality validation
- cleaning/conformance where required
- quality flags
- business-ready validated data

Required quality checks:

### Completeness

Check required fields including:

- customer email
- order customer_id
- order product_id

### Uniqueness

Check:

- customer_id
- order_id

### Referential Integrity

Validate:

- orders.customer_id against customers
- orders.product_id against products

Bad records must not simply be deleted.

The pipeline should preserve the affected records and identify their
quality status using appropriate quality indicators.

## Gold Layer

The Gold layer must provide business-level aggregations.

Required outputs:

### Sales by Product

Include:

- product_id
- product_name
- category
- total_orders
- total_revenue
- average_order_value

### Revenue by Customer

Include:

- customer_id
- customer_name
- customer_segment
- total_orders
- total_revenue
- average_order_value
- lifetime_value_actual

### Customer Segmentation

Include:

- customer_segment
- customer_count
- average_revenue
- total_revenue

## Dashboard

The Databricks SQL dashboard must include at least:

1. Top 10 Products by Revenue
2. Customer Revenue Distribution
3. Customer Segmentation

## Testing

Testing must verify that the intentional data-quality problems are
actually detected.

Examples include:

- missing required values
- duplicate identifiers
- invalid customer references
- invalid product references

## AI-Assisted Development

Cursor will be used throughout the project for:

- requirements analysis
- solution design
- data generation
- Bronze implementation
- Silver implementation
- Gold implementation
- testing
- debugging
- documentation

AI-generated output must be reviewed and validated before acceptance.

## Git

Git will be used to maintain incremental project history.

Commits should represent meaningful project stages such as:

- project setup
- requirements
- design
- data generation
- Bronze
- Silver
- Gold
- testing
- debugging
- dashboard
- documentation

## Security

Never place the following in source code or Git:

- passwords
- access tokens
- API keys
- Databricks personal access tokens
- database credentials
- other secrets

Use appropriate configuration or secret-management mechanisms when
credentials are eventually required.

## Working Principle

The project should be developed incrementally.

Do not generate the entire project in one step.

For each significant task:

1. Understand the requirement.
2. Define the approach.
3. Implement the smallest appropriate change.
4. Run and validate it.
5. Debug failures if necessary.
6. Document important decisions.
7. Commit the working change.