# Databricks Medallion Pipeline

End-to-end Databricks Medallion Architecture project implementing Bronze, Silver, Gold, Data Quality, Dashboard, and testing capabilities.

The project is designed to support both local execution and Databricks execution.

## 1. Project Overview

This project implements a layered data engineering pipeline using the Medallion Architecture:

```text
Raw CSV Files
     |
     v
  BRONZE
     |
     | Data ingestion + metadata
     v
  SILVER
     |
     | Cleansing + validation + DQ
     v
   GOLD
     |
     | Business aggregations
     v
 Analytics / Dashboard
````

The pipeline currently processes three datasets:

* Customers
* Orders
* Products

---

## 2. Technology Stack

* Python
* PySpark
* Delta Lake
* Databricks
* Databricks Unity Catalog
* SQL
* Git / GitHub
* pytest
* Power BI / Dashboard assets

---

## 3. Repository Structure

```text
databricks-medallion-pipeline/
|
├── ai-prompts/
|
├── configs/
|
├── cursor-workflow/
|
├── data/
│   ├── manifests/
│   └── raw/
|
├── documentation/
|
├── notebooks/
│   ├── 02_bronze_ingest.py
│   ├── 03_silver_transform.py
│   └── 04_gold_transform.py
|
├── resources/
│   └── dashboard/
|
├── src/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── common/
|
├── tests/
|
├── candidate-info.md
├── data-model.md
├── data-quality-strategy.md
├── design-notes.md
├── debugging-notes.md
├── final-ai-usage-summary.md
├── reflection.md
├── requirements.txt
└── README.md
```

---

# 4. Databricks Execution

The pipeline supports Databricks execution using:

```text
execution_mode = databricks
```

The Databricks implementation uses Unity Catalog tables and Databricks Spark Connect.

### Databricks Catalog

```text
workspace
```

### Schemas

```text
workspace.bronze
workspace.silver
workspace.gold
workspace.dq
```

---

# 5. Raw Data

The raw CSV files are stored in the Databricks Volume:

```text
/Volumes/workspace/bronze/raw_data/
```

### Input Files

```text
/Volumes/workspace/bronze/raw_data/customers.csv
/Volumes/workspace/bronze/raw_data/orders.csv
/Volumes/workspace/bronze/raw_data/products.csv
```

---

# 6. Bronze Layer

The Bronze layer ingests the raw CSV files and adds ingestion metadata.

### Bronze Tables

```text
workspace.bronze.bronze_customers
workspace.bronze.bronze_orders
workspace.bronze.bronze_products
```

### Validated Bronze Row Counts

| Dataset   |    Rows |
| --------- | ------: |
| Customers |  10,015 |
| Orders    | 100,035 |
| Products  |     500 |

Bronze ingestion also records metadata such as:

* `_source_file`
* `_ingest_batch_id`
* `_ingest_timestamp`
* `_bronze_record_id`

---

# 7. Silver Layer

The Silver layer reads the Bronze tables, applies transformations and validation rules, and writes cleaned Delta tables.

### Silver Tables

```text
workspace.silver.silver_customers
workspace.silver.silver_orders
workspace.silver.silver_products
```

### Validated Silver Row Counts

| Dataset   |    Rows |
| --------- | ------: |
| Customers |  10,015 |
| Orders    | 100,035 |
| Products  |     500 |

### Data Quality Summary

The current validation produced:

| Dataset   | Total Records | Valid Records | Invalid Records |
| --------- | ------------: | ------------: | --------------: |
| Customers |        10,015 |         9,935 |              80 |
| Orders    |       100,035 |        99,415 |             620 |
| Products  |           500 |           500 |               0 |

---

# 8. Data Quality Layer

Data Quality metrics are persisted in Unity Catalog tables.

### DQ Tables

```text
workspace.dq.dq_metrics
workspace.dq.dq_metrics_by_rule
```

### DQ Metrics

`workspace.dq.dq_metrics` contains dataset-level metrics including:

* `metric_run_id`
* `metric_timestamp`
* `dataset`
* `total_records`
* `valid_records`
* `invalid_records`
* `valid_record_pct`

### DQ Metrics by Rule

`workspace.dq.dq_metrics_by_rule` contains rule-level results including:

* `metric_run_id`
* `dataset`
* `rule_code`
* `rule_category`
* `failed_record_count`
* `expected_failed_count`

Example rule categories include:

* Completeness
* Uniqueness
* Referential Integrity

---

# 9. Gold Layer

The Gold layer creates business-ready analytical datasets from the validated Silver data.

### Gold Tables

```text
workspace.gold.gold_sales_by_product
workspace.gold.gold_revenue_by_customer
workspace.gold.gold_customer_segmentation
```

### Validated Gold Results

| Gold Table                   |  Rows |
| ---------------------------- | ----: |
| `gold_sales_by_product`      |   500 |
| `gold_revenue_by_customer`   | 9,935 |
| `gold_customer_segmentation` |     4 |

---

# 10. Pipeline Execution

The Databricks pipeline should be executed in the following order:

```text
02_bronze_ingest
       |
       v
03_silver_transform
       |
       v
04_gold_transform
       |
       v
Dashboard / Analytics
```

### Step 1 — Bronze

Run:

```text
notebooks/02_bronze_ingest.py
```

Expected outputs:

```text
workspace.bronze.bronze_customers
workspace.bronze.bronze_orders
workspace.bronze.bronze_products
```

---

### Step 2 — Silver

Run:

```text
notebooks/03_silver_transform.py
```

Expected outputs:

```text
workspace.silver.silver_customers
workspace.silver.silver_orders
workspace.silver.silver_products

workspace.dq.dq_metrics
workspace.dq.dq_metrics_by_rule
```

---

### Step 3 — Gold

Run:

```text
notebooks/04_gold_transform.py
```

Expected outputs:

```text
workspace.gold.gold_sales_by_product
workspace.gold.gold_revenue_by_customer
workspace.gold.gold_customer_segmentation
```

---

# 11. Databricks Notebook Configuration

The Databricks notebooks configure the repository source directory:

```text
/Workspace/Users/<user>/databricks-medallion-pipeline/src
```

The notebooks add this directory to `sys.path` so that project modules can be imported:

```python
from common.config import ...
from common.spark_session import ...
from silver.run_silver import ...
from gold.run_gold import ...
```

The Databricks execution mode is explicitly configured using:

```python
EXECUTION_MODE_DATABRICKS
```

---

# 12. Local vs Databricks Execution

The project supports two execution modes:

```text
local
databricks
```

### Local Mode

Local mode uses filesystem-based Delta paths and local Spark configuration.

### Databricks Mode

Databricks mode uses:

```text
Catalog: workspace

Bronze: workspace.bronze
Silver: workspace.silver
Gold:   workspace.gold
DQ:     workspace.dq
```

Databricks notebooks use the active Databricks Spark Connect session rather than configuring a local Spark master.

---

# 13. Configuration

The main configuration is handled through:

```text
src/common/config.py
```

Important configuration values include:

```text
MEDALLION_EXECUTION_MODE
DATABRICKS_CATALOG
BRONZE_SCHEMA
SILVER_SCHEMA
GOLD_SCHEMA
DQ_SCHEMA
MEDALLION_DELTA_PATH
```

For Databricks execution, the primary catalog is:

```text
workspace
```

---

# 14. Testing

The project uses `pytest` for automated testing.

Tests are located under:

```text
tests/
```

Run tests locally with:

```bash
pytest
```

The test suite covers pipeline components including configuration, transformations, data quality logic, and Gold-layer calculations.

---

# 15. Data Architecture

```text
                     +----------------------+
                     |   Raw CSV Files      |
                     | customers.csv        |
                     | orders.csv           |
                     | products.csv         |
                     +----------+-----------+
                                |
                                v
                  +--------------------------+
                  |         BRONZE            |
                  | workspace.bronze          |
                  |                           |
                  | bronze_customers          |
                  | bronze_orders             |
                  | bronze_products           |
                  +------------+--------------+
                               |
                               v
                  +--------------------------+
                  |         SILVER            |
                  | workspace.silver          |
                  |                           |
                  | silver_customers          |
                  | silver_orders             |
                  | silver_products           |
                  +------------+--------------+
                               |
                    +----------+----------+
                    |                     |
                    v                     v
          +-------------------+    +-------------------+
          |    DQ Layer       |    |      GOLD         |
          | workspace.dq      |    | workspace.gold    |
          |                   |    |                   |
          | dq_metrics        |    | sales_by_product  |
          | dq_metrics_by_rule|    | revenue_customer  |
          +-------------------+    | customer_segment  |
                                   +---------+---------+
                                             |
                                             v
                                  +----------------------+
                                  | Analytics / Dashboard|
                                  +----------------------+
```

---

# 16. Current Validation Status

The following pipeline stages have been successfully validated in Databricks:

* [x] Bronze ingestion
* [x] Bronze Unity Catalog tables
* [x] Silver transformation
* [x] Silver Unity Catalog tables
* [x] Data Quality metrics
* [x] Data Quality rule metrics
* [x] Gold transformation
* [x] Gold Unity Catalog tables

Current validated Gold outputs:

```text
workspace.gold.gold_sales_by_product
    500 rows

workspace.gold.gold_revenue_by_customer
    9,935 rows

workspace.gold.gold_customer_segmentation
    4 rows
```

---

# 17. Project Documentation

Detailed phase-specific documentation is available in:

```text
05-silver.md
06-gold.md
07-dashboard.md
08-testing.md
09-debugging.md
10-reflection.md
```

Additional project documentation includes:

```text
candidate-info.md
data-model.md
data-quality-strategy.md
design-notes.md
debugging-notes.md
final-ai-usage-summary.md
reflection.md
```

---

# 18. Git Workflow

The project is maintained using Git and GitHub.

Typical workflow:

```bash
git status

git add .

git commit -m "Update Databricks pipeline"

git push origin master
```

Before pulling changes into Databricks, ensure the local changes have been committed and pushed to GitHub.

---

# 19. Current Project Status

The project currently has a validated end-to-end:

```text
Raw
 ↓
Bronze
 ↓
Silver
 ↓
DQ
 ↓
Gold
```

Databricks execution has been validated using Unity Catalog under the `workspace` catalog.

The next development stages can build on the validated Gold layer for dashboard, analytics, testing, and final project documentation.
