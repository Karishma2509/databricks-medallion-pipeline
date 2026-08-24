# Phase 6 — Bronze Layer

## Objective

Implement the Bronze layer of the medallion architecture to ingest raw
CSV datasets into Delta format while preserving source fidelity.

## Datasets

The Bronze layer ingests:

- Customers
- Orders
- Products

## Bronze Design Principles

The Bronze layer must:

- Preserve all source records.
- Preserve duplicate records.
- Preserve null/missing values.
- Preserve invalid foreign-key references.
- Perform no business-level filtering.
- Perform no deduplication.
- Add ingestion metadata.
- Store data in Delta format.

## Bronze Metadata

Each Bronze record contains:

- source_name
- source_file
- ingest_batch_id
- ingest_timestamp
- bronze_record_id

`bronze_record_id` provides a deterministic identifier for the ingested
record.

## Implementation

Main implementation files:

- `src/bronze/ingest.py`
- `src/bronze/schemas.py`
- `src/bronze/run_bronze.py`
- `src/bronze/__init__.py`

Shared utilities:

- `src/common/config.py`
- `src/common/spark_session.py`
- `src/common/windows_hadoop.py`

Notebook:

- `notebooks/02_bronze_ingest.py`

## Testing

Bronze tests are implemented in:

`tests/test_bronze.py`

The Bronze test suite validates:

1. All three datasets are ingested.
2. Bronze row counts match source counts.
3. Required business columns exist.
4. Bronze metadata columns exist.
5. Bronze metadata is populated.
6. Duplicate customer IDs are preserved.
7. Duplicate order IDs are preserved.
8. Missing values are preserved.
9. Invalid references are preserved.
10. No filtering or deduplication occurs.
11. Bronze record ID format is valid.
12. Source CSV values are preserved.

## Validation Result

Full test suite:

`22 passed in 36.34s`

Bronze-specific tests:

`12 passed in 25.99s`

Phase 5 data-generation tests:

`10 passed`

Therefore, Phase 5 and Phase 6 are fully validated.

## Windows Local Spark Support

Local Spark execution on Windows requires Java and Hadoop native
support.

The project provides:

`src/common/windows_hadoop.py`

This provisions the required Hadoop binaries under:

`.tools/hadoop/`

The directory is gitignored and must not be committed.

Required binaries include:

- `winutils.exe`
- `hadoop.dll`

Java 17 is used for local Spark execution.

## Git Commit

Phase 6 implementation was committed as:

`599e493 Implement Phase 6 Bronze ingestion`

Working tree is clean after the Phase 6 commit.