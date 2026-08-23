# Requirements Analysis — Databricks Medallion Pipeline

**Project:** Databricks Medallion Pipeline — GenAI Coding Evaluation  
**Sources:** `cursor-workflow/project-context.md`, `cursor-workflow/spec.md`, `cursor-workflow/cursor-rules-or-instructions.md`, `cursor-workflow/task-breakdown.md`  
**Repository state at analysis:** Scaffolding exists (`src/`, `tests/`, `data/`, `configs/`, etc.); implementation artifacts are not yet populated.

---

## 1. Functional Requirements

### Explicit requirements

- Build an end-to-end e-commerce sales data pipeline using Databricks Medallion Architecture.
- Process three CSV datasets: `customers.csv`, `orders.csv`, `products.csv`.
- Follow the architecture flow: CSV Source → Bronze → Silver → Gold → Databricks SQL Dashboard.
- Generate source data with intentional data-quality problems (~700 problematic records) for Silver-layer detection.
- Bronze must ingest all three datasets.
- Silver must validate and conform Bronze data.
- Gold must provide three business-level aggregations: Sales by Product, Revenue by Customer, Customer Segmentation.
- Deliver a Databricks SQL dashboard with at least three required visualizations.
- Develop incrementally; do not generate the entire project in one step.
- Implement only the requested task; do not silently introduce additional requirements.
- Never place passwords, access tokens, API keys, Databricks personal access tokens, database credentials, or other secrets in source code or Git.

### Implementation decisions

- Orchestration approach (notebooks vs. modular Python packages vs. jobs).
- Databricks workspace layout (catalog, schema, table naming).
- Task sequencing and commit granularity within each phase.
- Data generator technology and how the ~700 issues are distributed across datasets and check types.
- Whether Bronze ingestion is one job or separate jobs per dataset.
- Silver table design (single table with flags vs. valid/quarantine split).
- Gold delivery as materialized Delta tables vs. views; refresh strategy.
- Dashboard layout, chart types, and optional filters.
- Secret-management mechanism when credentials are eventually required.
- How to gate each commit or pull request to a single phase or task.

---

## 2. Data Requirements

### Explicit requirements

- Three CSV source files: `customers.csv`, `orders.csv`, `products.csv`.
- Approximate scale: ~10,000 customers, ~100,000 orders, ~500 products.
- Approximately 700 intentionally problematic records for Silver to identify.
- **customers.csv** must include: `customer_id`, `customer_name`, `email`, and customer-related attributes required for segmentation.
- **orders.csv** must include: `order_id`, `customer_id`, `product_id`, and order-related measures required for revenue calculations.
- **products.csv** must include: `product_id`, `product_name`, `category`, and product-related attributes required for sales analysis.
- Bronze onward must use Delta format.
- Data must support traceability to the source.

### Implementation decisions

- CSV file location (e.g. `data/`) and naming conventions.
- Whether exact row counts (10,000 / 100,000 / 500) are required or approximate counts are acceptable.
- How many problematic records belong to each dataset and each issue type.
- Full schemas, data types, and definitions for segmentation and revenue fields.
- Delta partitioning, table properties, and Unity Catalog vs. Hive metastore.
- Specific ingestion metadata and lineage fields (source file name, row number, load timestamp, batch ID, etc.).
- Join keys and handling of bad Silver records in Gold calculations.

---

## 3. Bronze-Layer Requirements

### Explicit requirements

- Read the CSV source files.
- Preserve source records.
- Store the data in Delta format.
- Add ingestion metadata.
- Provide traceability to the source.
- Do not silently clean or remove source-quality issues.
- Do not modify Bronze merely to make downstream validation pass.

### Implementation decisions

- CSV read options (header, delimiter, encoding, infer schema vs. explicit schema).
- Whether to retain raw string columns alongside typed columns.
- Table paths, overwrite vs. append, and idempotency behavior.
- Which metadata columns to add and how they are named.
- How Bronze row identity is established for lineage.
- Validation scope (row counts, schemas) and test approach.

---

## 4. Silver-Layer Requirements

### Explicit requirements

- Validate and conform Bronze data.
- **Completeness:** identify missing required values — customer `email`; orders `customer_id`; orders `product_id`.
- **Uniqueness:** identify duplicate identifiers — `customer_id`; `order_id`.
- **Referential integrity:** validate `orders.customer_id` against `customers.customer_id`; validate `orders.product_id` against `products.product_id`.
- Bad records must not be silently deleted; preserve affected records and identify quality status using appropriate quality indicators.
- Provide quality indicators and measurable quality metrics.
- Implement quality checks incrementally.
- Do not combine unrelated quality checks into one opaque transformation.

### Implementation decisions

- Scope of “conformance” (type casting, trimming, standardization only vs. broader cleaning).
- Whether other fields beyond those listed are required.
- Null vs. blank-string handling for completeness checks.
- Duplicate resolution rule (flag all duplicates, first-wins, etc.).
- Flag design: boolean columns, reason codes, separate quarantine tables.
- Where quality metrics are stored (table, notebook output, test assertions).
- Module and function boundaries for incremental check implementation.

---

## 5. Gold-Layer Requirements

### Explicit requirements

**Sales by Product** must include:

- `product_id`
- `product_name`
- `category`
- `total_orders`
- `total_revenue`
- `average_order_value`

**Revenue by Customer** must include:

- `customer_id`
- `customer_name`
- `customer_segment`
- `total_orders`
- `total_revenue`
- `average_order_value`
- `lifetime_value_actual`

**Customer Segmentation** must include:

- `customer_segment`
- `customer_count`
- `average_revenue`
- `total_revenue`

Gold outputs must be business-oriented; business calculations must be explainable and testable.

### Implementation decisions

- Join paths from Silver tables to produce each Gold output.
- Whether Gold uses only Silver rows passing all quality checks or applies a different filter policy.
- Definition and calculation of `average_order_value`.
- Definition of `lifetime_value_actual` (e.g. whether it equals `total_revenue` or has a separate rule).
- Source and definition of `customer_segment`.
- Handling of customers with zero orders in segmentation aggregates.
- Rounding, currency precision, and any date filters.
- Materialized tables vs. views and refresh strategy.

---

## 6. Data-Quality Requirements

### Explicit requirements

- The implementation must demonstrate that intentional data-quality issues are detected.
- Test strategy must cover: completeness failures, uniqueness failures, referential-integrity failures, quality metric calculations.
- Examples of issues to detect: missing required values, duplicate identifiers, invalid customer references, invalid product references.
- Never hide data-quality problems by deleting bad records.
- Quality issues must be identified, flagged, measurable, and documented.

### Implementation decisions

- How tests align to the ~700 known bad records and expected counts per issue type.
- Full rule catalog and severity levels beyond the listed examples.
- Whether to check referential integrity within customers or products tables (not specified).
- Where quality metrics are published and how they are validated.
- Content and structure of `data-quality-strategy.md`.

---

## 7. Dashboard Requirements

### Explicit requirements

- Platform: Databricks SQL Dashboard.
- Required visualizations:
  1. Top 10 Products by Revenue
  2. Customer Revenue Distribution
  3. Customer Segmentation
- Assemble the visualizations into a Databricks SQL dashboard.

### Implementation decisions

- Lakeview vs. legacy SQL dashboard.
- Chart types, sort order, and time range for Top 10 Products.
- Definition and visualization approach for Customer Revenue Distribution (bins, histogram, percentiles, outliers).
- Chart type for Customer Segmentation (bar, pie, table, etc.).
- Whether Gold tables are queried directly or through a semantic layer.
- Dashboard layout and optional filters (not required beyond the three visualizations).

---

## 8. Testing Requirements

### Explicit requirements

- Testing must verify that intentional data-quality problems are actually detected.
- Examples to cover: missing required values, duplicate identifiers, invalid customer references, invalid product references.
- Test source-data generation, Bronze ingestion, completeness checks, uniqueness checks, referential integrity, and Gold calculations.
- Every significant transformation should have validation.
- On test failure: inspect the error, identify root cause, make the smallest appropriate change, re-run the test, document the result when relevant.
- Bronze validation includes row counts and schemas.

### Implementation decisions

- Test framework (pytest, notebook assertions, Databricks jobs).
- Exact expected counts for ~700 issues and acceptable tolerance.
- Unit vs. integration tests; local Spark vs. Databricks runtime.
- Golden-file or fixture-based expected aggregates for Gold.
- Coverage threshold for “every significant transformation.”
- Where debugging outcomes are recorded (`debugging-notes.md` vs. other locations).

---

## 9. Documentation Requirements

### Explicit requirements

- Document important decisions.
- Record AI prompts and significant AI-assisted decisions in the `ai-prompts` directory.
- Document the data-generation approach.
- Document debugging decisions when relevant.
- Before implementing a task, consider: `cursor-workflow/project-context.md`, `cursor-workflow/spec.md`, `requirements-analysis.md`, `design-notes.md`, `data-model.md`, `data-quality-strategy.md`.
- Finalization includes: review Git history, complete AI prompt history, complete reflection, complete final AI usage summary, update README, prepare final submission artifacts.

### Implementation decisions

- Format and depth for `design-notes.md`, `data-model.md`, and `data-quality-strategy.md`.
- When each referenced document is authored relative to implementation.
- README structure and run instructions.
- Templates for `reflection.md` and `final-ai-usage-summary.md`.

---

## 10. Git / Version-Control Expectations

### Explicit requirements

- Use Git to maintain incremental project history.
- Commits should represent meaningful project stages: project setup, requirements, design, data generation, Bronze, Silver, Gold, testing, debugging, dashboard, documentation.
- Make meaningful commits after stable project milestones.
- Do not create meaningless commits for every small change.
- Never commit secrets.

### Implementation decisions

- Branch strategy (main only vs. feature branches).
- Commit message conventions.
- Granularity of commits within a single phase.
- `.gitignore` rules for local config, tokens, and large generated data.

---

## 11. AI-Assisted Development Expectations

### Explicit requirements

- Use Cursor throughout the project for: requirements analysis, solution design, data generation, Bronze implementation, Silver implementation, Gold implementation, testing, debugging, documentation.
- AI-generated output must be reviewed and validated before acceptance.
- Do not assume generated code is correct; review, understand, run, and validate before accepting.
- If generated code is rejected or modified, document why.
- Identify ambiguities before implementing them.
- Use PySpark and Spark SQL appropriately for Databricks.

### Implementation decisions

- Review checklist for AI-generated changes.
- Where to log rejected or modified AI output (`ai-prompts` vs. `design-notes.md`).
- Notebook vs. `src/` module layout for PySpark code.
- Cursor model or settings per task (not specified in project docs).

---

## 12. Assumptions

The following assumptions are reasonable given the documentation but are **not explicitly specified**. They should be confirmed or replaced during solution design.

1. **Databricks runtime:** PySpark on Databricks is implied by cursor-rules; local development and CI approach are not defined.
2. **Revenue calculation:** Orders require a monetary measure; the exact field name and formula (e.g. quantity × unit price) are not defined in the spec.
3. **`lifetime_value_actual`:** Likely represents total historical revenue per customer, but its relationship to `total_revenue` is not formally defined.
4. **`customer_segment`:** Required for Gold outputs, but segmentation rules (RFM, spend tiers, etc.) are not defined in the data-generation requirements.
5. **Scale tolerance:** Documentation uses approximate counts (~10,000 / ~100,000 / ~500); whether exact counts are required is unspecified.
6. **Orchestration:** No requirement mandates Databricks Workflows, Delta Live Tables, or CI/CD; only the end-to-end outcome is required.
7. **Unity Catalog:** Not mentioned in the spec; catalog and schema naming remain open.
8. **Existing scaffold:** Repository folders and placeholder files exist; implementation has not yet started in `src/`, `tests/`, or `data/`.

---

## 13. Open Ambiguities

These items are unclear in the project documentation and must be resolved in design before implementation.

| Topic | What is known | What is ambiguous |
|---|---|---|
| Gold input filter | Silver preserves bad records; Gold needs business aggregates | Whether Gold uses only rows passing all DQ checks, or excludes flagged rows at query time |
| ~700 bad records | Total intentional issues for Silver detection | Split across datasets and issue types |
| Silver “conformance” | Silver validates and conforms Bronze | Scope of cleaning vs. validation-only |
| Customer Revenue Distribution | Required dashboard visualization | Chart type and definition of “distribution” |
| Duplicate handling | Duplicates must be identified, not silently removed | Resolution or ranking rule when duplicates exist |
| Referential integrity scope | Orders → customers and orders → products | Whether internal RI within customers or products is required |
| Bronze validation | Row counts and schemas (task-breakdown) | Tolerance for approximate source scale |
| Quality metrics | Must be measurable | Exact metric definitions and storage location |

### Constraints to respect (not ambiguities)

- Bronze must not clean data to fix quality issues.
- Silver must not delete bad records.
- Development must proceed incrementally, not as a single bulk delivery.

---

## 14. Proposed Acceptance Criteria

Measurable criteria by major project phase, aligned with `cursor-workflow/task-breakdown.md`. Thresholds use documented targets where stated; others are proposed for design confirmation.

### Phase 1 — Local Setup

- Git is installed and the repository is available locally.
- Repository opens in Cursor without configuration errors.
- `git status` runs successfully.

### Phase 2 — Project Foundation

- Repository structure matches the intended layout from task-breakdown.
- `cursor-workflow/` documentation is present.
- A baseline Git commit exists.
- No secrets appear in tracked files.

### Phase 3 — Requirements Analysis

- This document is complete.
- Explicit requirements, implementation decisions, assumptions, and ambiguities are separated.
- Acceptance criteria are defined per major phase.

### Phase 4 — Solution Design

- Medallion architecture and data flow are documented.
- Source-to-target mappings and schemas are defined for all three entities.
- Data-quality strategy covers completeness, uniqueness, referential integrity, flagging, and metrics.
- Open ambiguities (revenue, LTV, segments, Gold filter policy) are resolved in design artifacts.

### Phase 5 — Data Generation

- `customers.csv` contains approximately 10,000 rows.
- `orders.csv` contains approximately 100,000 rows.
- `products.csv` contains approximately 500 rows.
- Approximately 700 intentional data-quality issues are present and traceable.
- Data-generation approach is documented.
- Validation confirms row counts and presence of each required issue type.

### Phase 6 — Bronze

- Three Delta tables are created from the CSV sources.
- Row counts match source CSVs (no records dropped).
- Ingestion metadata is populated on every row.
- Schemas are documented and validated by tests.
- No data-quality cleaning is applied in Bronze.

### Phase 7 — Silver

- Completeness checks detect missing `email`, `customer_id`, and `product_id` as specified.
- Uniqueness checks detect duplicate `customer_id` and `order_id`.
- Referential-integrity checks detect orphan `orders.customer_id` and `orders.product_id`.
- All Bronze rows are preserved in Silver (or equivalent auditable preservation).
- Quality metrics report counts consistent with known intentional issues.
- Checks are implemented incrementally with test coverage per check type.

### Phase 8 — Gold

- Three Gold outputs exist with all required columns per spec.
- `average_order_value` is calculated per the documented design (e.g. `total_revenue / total_orders` where `total_orders > 0`).
- Business logic is documented and covered by tests with known expected aggregates on fixture or sample data.

### Phase 9 — Dashboard

- One Databricks SQL dashboard is published with all three required visualizations.
- Top 10 Products by Revenue shows at most 10 products ranked by revenue.
- Customer Revenue Distribution renders from Gold customer revenue data.
- Customer Segmentation visualization uses the Gold segmentation output.

### Phase 10 — Testing

- Automated tests pass for data generation, Bronze ingestion, each Silver quality rule, and Gold calculations.
- Tests assert detection of missing values, duplicate identifiers, and invalid foreign-key references.
- Quality metric calculations are verified against expected counts.

### Phase 11 — Debugging

- Test failures are logged in `debugging-notes.md` with root cause and fix.
- Full test suite passes after fixes.
- Fixes are minimal and scoped to the failing behavior.

### Phase 12 — Finalization

- Git history shows meaningful stage commits across requirements, design, data generation, Bronze, Silver, Gold, dashboard, testing, and documentation.
- `README.md` describes setup, run order, and validation steps.
- `ai-prompts/` is complete; `reflection.md` and `final-ai-usage-summary.md` are filled in.
- Submission artifacts are ready and no credentials are present in the repository.
