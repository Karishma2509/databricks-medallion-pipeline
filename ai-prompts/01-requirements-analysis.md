# Requirements Analysis — Cursor Prompt History

## Prompt 1 — Initial Requirements Analysis

### Prompt Sent to Cursor
You are helping me implement a Databricks Medallion Architecture project
for a GenAI coding evaluation.

Before writing any code, analyze the project requirements.

Read these files first:

- cursor-workflow/project-context.md
- cursor-workflow/spec.md
- cursor-workflow/cursor-rules-or-instructions.md
- cursor-workflow/task-breakdown.md

Also inspect the existing repository structure.

Do not generate implementation code yet.

I want you to produce a requirements analysis that identifies:

1. Functional requirements
2. Data requirements
3. Bronze-layer requirements
4. Silver-layer requirements
5. Gold-layer requirements
6. Data-quality requirements
7. Dashboard requirements
8. Testing requirements
9. Documentation requirements
10. Git/version-control expectations
11. AI-assisted development expectations
12. Important assumptions or ambiguities

For each requirement, clearly distinguish:
- what is explicitly specified
- what is an implementation decision we need to make

Do not invent requirements that are not supported by the project
documentation.

At the end, propose measurable acceptance criteria for each major
project phase.

Do not write code yet.

### Cursor Response
# Requirements Analysis — Databricks Medallion Pipeline (GenAI Evaluation)

This analysis is based on:

- `cursor-workflow/project-context.md`
- `cursor-workflow/spec.md`
- `cursor-workflow/cursor-rules-or-instructions.md`
- `cursor-workflow/task-breakdown.md`

Repository inspection shows scaffolding only: folder structure exists (`src/bronze`, `src/silver`, `src/gold`, `src/data_generation`, `tests`, `data`, `notebooks`, `configs`, etc.), but implementation files, CSVs, and most documentation placeholders are empty.

---

## 1. Functional Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| End-to-end e-commerce sales pipeline | Yes — process customers, orders, products through Medallion layers to a dashboard | Orchestration model (notebooks vs. jobs vs. modular Python packages) |
| Medallion flow: CSV → Bronze → Silver → Gold → Databricks SQL Dashboard | Yes | Databricks workspace layout (catalog/schema/table naming) |
| Incremental development | Yes — do not build entire project in one step | Task sequencing within each phase |
| Data generation with intentional quality issues | Yes — ~700 problematic records for Silver to detect | Generator technology, issue distribution across check types |
| Bronze ingestion for all three datasets | Yes | Single vs. separate ingestion jobs/notebooks |
| Silver validation and conformance | Yes | Table design (single table vs. valid/quarantine split) |
| Gold business aggregations (3 outputs) | Yes — Sales by Product, Revenue by Customer, Customer Segmentation | Materialized tables vs. views; refresh strategy |
| Databricks SQL dashboard | Yes — 3 required visualizations | Dashboard layout, chart types, filters |
| Security: no secrets in source/Git | Yes | Secret storage mechanism when credentials are needed |
| Scope discipline | Yes — implement only requested task; no silent extra requirements | How to gate each PR/commit to a single phase |

---

## 2. Data Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Three CSV sources: `customers.csv`, `orders.csv`, `products.csv` | Yes | File location (e.g. `data/`), naming conventions |
| Scale: ~10,000 customers, ~100,000 orders, ~500 products | Yes (approximate) | Exact counts; whether “~” is acceptable |
| ~700 intentionally problematic records total | Yes | How many per dataset and per issue type |
| **customers.csv** fields | Partial — `customer_id`, `customer_name`, `email`, plus attributes for segmentation | Full schema, data types, `customer_segment` definition |
| **orders.csv** fields | Partial — `order_id`, `customer_id`, `product_id`, plus measures for revenue | Revenue field name(s), quantity, order date, currency |
| **products.csv** fields | Partial — `product_id`, `product_name`, `category`, plus sales attributes | Price/unit fields, additional attributes |
| Delta as storage format (Bronze onward) | Yes | Partitioning, table properties, Unity Catalog vs. Hive metastore |
| Traceability to source | Yes | Source file name, row number, load timestamp, batch ID, etc. |
| Gold field lists | Yes — see sections 5 and spec | Join keys, handling of bad Silver records in Gold |

---

## 3. Bronze-Layer Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Read raw CSV files | Yes | Read options (header, delimiter, encoding, infer schema vs. explicit schema) |
| Preserve source records | Yes | Whether to keep raw string columns alongside typed columns |
| Store as Delta | Yes | Table paths, overwrite vs. append, idempotency |
| Add ingestion metadata | Yes | Which metadata columns and naming |
| Support traceability | Yes | Lineage fields and uniqueness of Bronze row identity |
| Do not silently clean or remove quality issues | Yes | Whether to add Bronze-level DQ flags (spec implies no cleaning) |
| Do not modify Bronze to make downstream validation pass | Yes (cursor-rules) | Validation limited to row counts/schemas per task-breakdown |

---

## 4. Silver-Layer Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Validate and conform Bronze data | Yes | “Conform” scope (type casting, trimming, standardization only?) |
| **Completeness** — missing required values | Yes — customer `email`; orders `customer_id`, `product_id` | Other required fields; null vs. blank handling |
| **Uniqueness** — duplicate identifiers | Yes — `customer_id`, `order_id` | Duplicate resolution rule (first wins, flag all, etc.) |
| **Referential integrity** | Yes — `orders.customer_id` → customers; `orders.product_id` → products | Orphan handling in Silver vs. Gold |
| Preserve bad records; do not silently delete | Yes | Flag design: boolean columns, reason codes, separate quarantine tables |
| Quality indicators and measurable metrics | Yes | Metric definitions (pass rate, counts by rule, dashboards/logs) |
| Implement checks incrementally | Yes (cursor-rules) | Order of implementation; one check per commit vs. per module |
| Do not combine unrelated checks into one opaque transformation | Yes (cursor-rules) | Module/function boundaries |

---

## 5. Gold-Layer Requirements

### Sales by Product

| Field | Explicitly specified | Implementation decision needed |
|---|---|---|
| `product_id`, `product_name`, `category` | Yes | Source join path (Silver products + orders) |
| `total_orders`, `total_revenue`, `average_order_value` | Yes | Whether failed RI orders are excluded; AOV formula |

### Revenue by Customer

| Field | Explicitly specified | Implementation decision needed |
|---|---|---|
| `customer_id`, `customer_name`, `customer_segment` | Yes | Segment source field and join logic |
| `total_orders`, `total_revenue`, `average_order_value`, `lifetime_value_actual` | Yes | Whether LTV equals total_revenue or has a separate definition |

### Customer Segmentation

| Field | Explicitly specified | Implementation decision needed |
|---|---|---|
| `customer_segment`, `customer_count`, `average_revenue`, `total_revenue` | Yes | Aggregation grain; customers with zero orders |

| Cross-cutting | Explicitly specified | Implementation decision needed |
|---|---|---|
| Business-oriented, explainable, testable calculations | Yes (cursor-rules) | Rounding, currency precision, date filters |
| Only validated/clean data vs. all data | Not specified | Filter policy for Gold inputs |

---

## 6. Data-Quality Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Detect intentional issues from generated data | Yes | Test fixtures aligned to ~700 known bad records |
| Completeness failures | Yes — examples listed | Full rule catalog and severity |
| Uniqueness failures | Yes — `customer_id`, `order_id` | Composite keys not mentioned |
| Referential-integrity failures | Yes — invalid customer/product references | Whether to check products/customers internal RI |
| Quality metrics | Yes — “measurable” | Where metrics live (table, notebook output, tests) |
| Never hide DQ problems by deleting records | Yes (cursor-rules, spec) | How Gold treats flagged Silver rows |
| Document DQ strategy | Implied by cursor-rules + task-breakdown Phase 4 | `data-quality-strategy.md` content |

---

## 7. Dashboard Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Platform: Databricks SQL Dashboard | Yes | Lakeview vs. legacy SQL dashboard |
| **1. Top 10 Products by Revenue** | Yes | Chart type, sort order, time range |
| **2. Customer Revenue Distribution** | Yes | Bins, histogram vs. percentile, outliers |
| **3. Customer Segmentation** | Yes | Chart type (bar, pie, table) |
| Data source | Implied — Gold tables | Direct SQL on Gold vs. semantic layer |
| Minimum of three visualizations | Yes | Additional KPIs not required |

---

## 8. Testing Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Verify intentional DQ problems are detected | Yes | Test framework (pytest, notebook assertions, Databricks jobs) |
| Cover: missing values, duplicates, invalid customer/product refs | Yes | Exact expected counts for ~700 issues |
| Test source data generation | Yes (task-breakdown) | Generation validation scripts |
| Test Bronze ingestion | Yes — row counts and schemas | Tolerance for approximate scale |
| Test completeness, uniqueness, RI | Yes | Unit vs. integration; local Spark vs. Databricks |
| Test Gold calculations | Yes | Golden-file expected aggregates |
| Every significant transformation should have validation | Yes (cursor-rules) | Coverage threshold |
| On failure: inspect, root cause, minimal fix, re-run, document | Yes (cursor-rules) | Where debugging notes are recorded |

---

## 9. Documentation Requirements

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Document important decisions | Yes | Format and location (`design-notes.md`, etc.) |
| Record AI prompts and significant AI decisions in `ai-prompts/` | Yes | One file per phase (already scaffolded) |
| Data generation approach | Yes (task-breakdown) | Level of detail |
| Debugging decisions when relevant | Yes | `debugging-notes.md` usage |
| Update README | Yes (task-breakdown Phase 12) | README structure |
| Final artifacts: reflection, AI usage summary | Yes (task-breakdown) | Templates for `reflection.md`, `final-ai-usage-summary.md` |
| Referenced docs before implementation | Yes (cursor-rules) — `requirements-analysis.md`, `design-notes.md`, `data-model.md`, `data-quality-strategy.md` | When each is authored relative to implementation |

---

## 10. Git / Version-Control Expectations

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Git for incremental project history | Yes | Branch strategy (main only vs. feature branches) |
| Meaningful commits at project stages | Yes — setup, requirements, design, data gen, Bronze, Silver, Gold, testing, debugging, dashboard, documentation | Commit message conventions |
| Meaningful milestones; avoid noise commits | Yes (cursor-rules) | Granularity within a phase |
| Baseline commit after foundation | Yes (task-breakdown Phase 2) | Whether foundation is already complete |
| Never commit secrets | Yes | `.gitignore` for local config, tokens, data if large |

---

## 11. AI-Assisted Development Expectations

| Requirement | Explicitly specified | Implementation decision needed |
|---|---|---|
| Cursor used across full lifecycle | Yes — analysis, design, generation, layers, testing, debugging, docs | Model/settings per task |
| Review and validate AI output before acceptance | Yes | Review checklist |
| Do not assume generated code is correct | Yes (cursor-rules) | Run/validate steps per change |
| Document rejected or modified AI code and why | Yes (cursor-rules) | Where to log (ai-prompts vs. design-notes) |
| Identify ambiguities before implementing | Yes (cursor-rules) | Escalation when blocked |
| Implement only requested task | Yes | Phase boundaries in prompts |
| Use PySpark / Spark SQL appropriately | Yes (cursor-rules) | Notebook vs. `src/` module layout |

---

## 12. Important Assumptions and Ambiguities

### Reasonable assumptions (not fully specified)

1. **Databricks runtime** — PySpark on Databricks is implied by cursor-rules; local development approach is not defined.
2. **Revenue calculation** — Orders need a monetary measure; field name and formula (e.g. `quantity × unit_price`) are not defined.
3. **`lifetime_value_actual`** — Likely total historical revenue per customer; not formally defined vs. `total_revenue`.
4. **`customer_segment`** — Required for Gold but segmentation rules (RFM, spend tiers, etc.) are not defined in source data generator requirements.
5. **Gold input filter** — Unclear whether Gold uses only Silver rows passing all DQ checks or all rows with flags excluded at query time.
6. **~700 bad records** — Total across all datasets/issue types; split not specified.
7. **“Approximately” scale** — Whether exact 10k/100k/500 or acceptable variance is unspecified.
8. **Silver “conformance”** — Scope of cleaning (trim, cast, normalize) vs. validation-only is not detailed.
9. **Dashboard “Customer Revenue Distribution”** — Visualization type and definition of “distribution” not specified.
10. **Orchestration** — No requirement for Databricks Workflows, Delta Live Tables, or CI/CD; only end-to-end outcome is required.
11. **Unity Catalog** — Not mentioned; catalog/schema naming is an open decision.
12. **Existing empty scaffold** — Folders and placeholder files exist; implementation has not started.

### Conflicts to avoid

- Bronze must not clean data; Silver must not delete bad records; cursor-rules reinforce both.
- Incremental delivery vs. complete pipeline — build phase by phase, not all at once.

---

## Proposed Measurable Acceptance Criteria by Phase

Criteria below map to `task-breakdown.md` phases. Thresholds use documented targets where stated; otherwise they are proposed and should be confirmed in design.

### Phase 1 — Local Setup
- Git installed and repository cloned/open in Cursor.
- `git status` runs without error.

### Phase 2 — Project Foundation
- Documented folder structure matches task-breakdown intent.
- `cursor-workflow/*` docs present; baseline Git commit exists.
- No secrets in tracked files.

### Phase 3 — Requirements Analysis
- This document completed with explicit vs. decision items separated.
- Assumptions and ambiguities listed.
- Acceptance criteria defined per phase.
- Recorded in `requirements-analysis.md` and `ai-prompts/01-requirements-analysis.md`.

### Phase 4 — Solution Design
- Architecture diagram and data flow documented.
- Source-to-target mappings and schemas defined for all three entities.
- DQ strategy covers completeness, uniqueness, RI, flagging, and metrics.
- Open ambiguities (revenue, LTV, segments, Gold filter) resolved in design.

### Phase 5 — Data Generation
- `customers.csv` ≈ 10,000 rows; `orders.csv` ≈ 100,000; `products.csv` ≈ 500.
- Exactly **700** (or documented total) intentional DQ issues injectable and traceable.
- Generation approach documented.
- Validation script confirms counts and presence of each issue type.

### Phase 6 — Bronze
- Three Delta tables created from CSVs.
- Row counts match source CSVs (no dropped rows).
- Ingestion metadata columns populated on every row.
- Schemas documented and validated by tests.
- No DQ cleaning applied in Bronze.

### Phase 7 — Silver
- Completeness flags detect missing `email`, `customer_id`, `product_id` as specified.
- Uniqueness flags detect duplicate `customer_id` and `order_id`.
- RI flags detect orphan `orders.customer_id` and `orders.product_id`.
- 100% of Bronze rows retained in Silver (or equivalent auditable preservation).
- Quality metrics report counts matching known ~700 issues (± agreed tolerance).
- Checks implemented incrementally with test coverage per check.

### Phase 8 — Gold
- Three Gold outputs exist with all required columns per spec.
- `average_order_value` = `total_revenue / total_orders` where orders > 0 (per design).
- Business logic documented and covered by tests with known expected aggregates on sample/fixture data.

### Phase 9 — Dashboard
- One Databricks SQL dashboard published with all three required visualizations.
- Top 10 Products shows ≤10 products ranked by revenue.
- Customer Revenue Distribution renders from Gold customer revenue data.
- Customer Segmentation visualization uses Gold segmentation output.

### Phase 10 — Testing
- Automated tests pass for: data generation, Bronze ingest, each Silver DQ rule, Gold calculations.
- Tests assert detection of missing values, duplicates, and invalid FK references.
- Quality metric calculations verified against expected counts.

### Phase 11 — Debugging
- Any test failures logged in `debugging-notes.md` with root cause and fix.
- Full test suite passes after fixes.
- Fixes are minimal and scoped to failing behavior.

### Phase 12 — Finalization
- Git history shows meaningful stage commits (requirements → design → data → Bronze → Silver → Gold → dashboard → tests → docs).
- `README.md` describes setup, run order, and validation steps.
- `ai-prompts/` complete; `reflection.md` and `final-ai-usage-summary.md` filled in.
- Submission artifacts ready; no credentials in repository.

---

## Summary

The project is clearly scoped as a **Medallion e-commerce pipeline** with **three CSV sources**, **Delta layers**, **Silver DQ with preservation of bad data**, **three Gold aggregates**, and a **three-widget Databricks SQL dashboard**, developed **incrementally** with **Git**, **tests**, and **documented AI-assisted workflow**.

The largest gaps to resolve in **Phase 4 (Design)** before coding are: full schemas, revenue/LTV definitions, customer segmentation rules, distribution of the ~700 DQ issues, Silver flag/metric design, Gold inclusion rules for failed DQ rows, and Databricks workspace/naming conventions.

No implementation code is included per your request. I can save this analysis to `requirements-analysis.md` and update the Cursor response section in `ai-prompts/01-requirements-analysis.md` if you want that documented next.

### Candidate Review

#### Accepted

- The separation between explicit requirements and implementation decisions.
- The identification of unresolved requirements such as revenue calculation,
  customer segmentation, LTV, and Gold inclusion rules.
- The identification of testing and Git requirements.
- The phased acceptance criteria structure.

#### Modified / To Be Confirmed

- Exact number of intentional data-quality issues.
- Exact source schemas.
- Revenue calculation.
- Lifetime value definition.
- Customer segmentation logic.
- Treatment of Silver quality failures in Gold.
- Dashboard visualization choices.
- Databricks table/catalog naming.
- Orchestration approach.

These items were not fully specified in the current project context and
must be resolved during the design phase rather than treated as confirmed
requirements.

#### Rejected

None at this stage.

#### Key Decision

Do not begin implementation until the major design ambiguities are
resolved.