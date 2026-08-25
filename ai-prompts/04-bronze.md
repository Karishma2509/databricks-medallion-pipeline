# Phase 6 — Bronze Layer — Cursor Prompt History

## Prompt 1 — Implement Bronze ingestion

### What I asked Cursor

```
Phase 5 CSVs are in data/raw/ (customers 10,015 / orders 100,035 / products 500).
Time for Phase 6 Bronze.

Read data-model.md, data-quality-strategy.md, design-notes.md, and the Bronze
section of cursor-workflow/task-breakdown.md.

Implement under src/bronze/ — business logic in src/, thin notebook in
notebooks/02_bronze_ingest.py (same pattern as other layers).

Bronze rules — don't bend these:
- Ingest customers.csv, orders.csv, products.csv
- Preserve every row: duplicates, nulls, bad FKs stay
- No filtering, no dedup, no DQ fixes
- Add ingestion metadata per data-model.md:
  _ingest_batch_id, _ingest_timestamp, _source_file, _source_row_number,
  _bronze_record_id
- Write Delta to data/delta/medallion_eval/bronze/ (configurable via
  src/common/config.py BronzeSettings)
- Row counts must match source exactly

Add tests/test_bronze.py with session-scoped Spark fixtures (same pattern
we'll reuse for Silver/Gold). Run pytest -v when done.

Don't touch Silver or Gold yet.
```

### What we built

| File | Role |
|---|---|
| `src/bronze/ingest.py` | CSV read, metadata, Delta write |
| `src/bronze/schemas.py` | Table definitions, CSV schemas |
| `src/bronze/run_bronze.py` | Entry point |
| `src/common/config.py` | `BronzeSettings`, paths |
| `src/common/spark_session.py` | Local Spark session |
| `src/common/windows_hadoop.py` | Windows Hadoop shim |
| `notebooks/02_bronze_ingest.py` | Thin orchestration |
| `tests/test_bronze.py` | 12 Bronze tests |

Tables: `bronze_customers`, `bronze_orders`, `bronze_products`.

Local write pattern:

```python
bronze_df.write.format("delta").mode("overwrite").save(str(delta_path))
```

**Tests:** all three datasets ingested, row counts, business + metadata columns, duplicates/missing values/invalid refs preserved, no filtering/dedup, `_bronze_record_id` format, CSV fidelity.

**Results at implementation time:** Bronze 12 passed; data gen 10 passed; full suite 22 passed in ~36s.

**Windows:** Java 17 + `src/common/windows_hadoop.py` → `.tools/hadoop/` (gitignored).

**Git:** `599e493 Implement Phase 6 Bronze ingestion`.

---

## Prompt 2 — Databricks Free Edition / Unity Catalog

### What I asked Cursor

```
Bronze works locally (data/raw → data/delta/medallion_eval/bronze/).
Colleagues need Databricks Free Edition with Unity Catalog. Support both modes
without duplicating business logic or breaking pytest.

Local (unchanged):
- Read CSVs from data/raw/
- Write/read Delta paths under data/delta/medallion_eval/bronze/

Databricks:
- Read CSVs from /Volumes/workspace/bronze/raw_data/
- Write workspace.bronze.bronze_customers, bronze_orders, bronze_products
  via saveAsTable()
- Read back with spark.table()
- Catalog/schema configurable — not hard-coded in ingest.py

Add execution_mode to BronzeSettings (we'll reuse this pattern for Silver).
Update notebooks/02_bronze_ingest.py to pass EXECUTION_MODE_DATABRICKS settings.
Row counts must stay: 10,015 / 100,035 / 500.

Don't change Bronze business rules. Don't modify Silver/Gold. pytest -v must
stay green.
```

### What changed

- `src/common/config.py` — `EXECUTION_MODE_LOCAL`, `EXECUTION_MODE_DATABRICKS`, `source_csv_uri()`, `bronze_storage_label()`
- `src/bronze/ingest.py` — `_write_bronze_table()`, `_read_bronze_row_count()`, mode-aware `read_bronze_table()`
- `src/bronze/run_bronze.py` — optional `settings` parameter
- `notebooks/02_bronze_ingest.py` — `run_bronze_ingestion(spark, settings=settings)`
- `tests/conftest.py` — `execution_mode=EXECUTION_MODE_LOCAL`

Business logic unchanged; I/O branches on mode only.

**Databricks env vars:**

```
MEDALLION_EXECUTION_MODE=databricks
DATABRICKS_CATALOG=workspace
BRONZE_SCHEMA=bronze
MEDALLION_RAW_VOLUME_PATH=/Volumes/workspace/bronze/raw_data
```

Validated in workspace: `workspace.bronze.bronze_*` with expected row counts.
