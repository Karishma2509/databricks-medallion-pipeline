# Phase 8 — Gold Layer — Cursor Prompt History

## Prompt 1 — Implement Gold aggregations

### What I asked Cursor

```
Silver is complete (silver_customers 10,015 / silver_orders 100,035 /
silver_products 500, plus dq_metrics tables). Phase 8 is Gold — business
aggregates only. Don't re-run Silver DQ rules in Gold.

Read data-model.md, data-quality-strategy.md, design-notes.md.
Use is_valid_record as the inclusion filter — don't reference individual DQ
flags in Gold.

Three Gold tables under data/delta/medallion_eval/gold/ (configurable via
GoldSettings in src/common/config.py):

gold_sales_by_product
- Drive from silver_products — every product gets a row (500 total)
- Left join valid-order aggregates (silver_orders WHERE is_valid_record = true)
- total_orders = COUNT(DISTINCT order_id)
- total_revenue = SUM(line_revenue)
- average_order_value = total_revenue / total_orders; null when total_orders = 0
- Zero-order products: total_orders = 0, total_revenue = 0, AOV null

gold_revenue_by_customer
- Valid customers only (is_valid_record = true)
- Left join valid-order aggregates so zero-order valid customers stay
- customer_segment from total_revenue:
    No Purchase: = 0
    Low Value: > 0 and < 500
    Mid Value: >= 500 and < 2000
    High Value: >= 2000
- lifetime_value_actual = total_revenue

gold_customer_segmentation
- Aggregate from gold_revenue_by_customer (not directly from Silver)
- customer_count, average_revenue, total_revenue per segment
- Exactly 4 segment rows

Exclusion policy:
- Invalid orders → excluded from all revenue/order rollups
- Invalid customers → not in gold_revenue_by_customer or segment counts
- Valid orders on invalid customers can still count toward product metrics
  if the order itself is valid
- No Bronze/Silver metadata or DQ columns in Gold output

Implement under src/gold/: filters.py, sales_by_product.py, revenue_by_customer.py,
customer_segmentation.py, transform.py, run_gold.py.
Thin notebook notebooks/04_gold_transform.py.
Add tests/test_gold.py, extend tests/conftest.py.
Run pytest -v. Don't touch dashboard yet.
```

### What we built

| Module | Role |
|---|---|
| `schemas.py` | Column lists, segment constants |
| `filters.py` | `valid_orders`, `valid_customers` |
| `sales_by_product.py` | `gold_sales_by_product` |
| `revenue_by_customer.py` | `gold_revenue_by_customer` + segment assignment |
| `customer_segmentation.py` | `gold_customer_segmentation` |
| `transform.py` | Pipeline orchestration |
| `run_gold.py` | Entry point |

**`gold_sales_by_product`:** `product_id`, `product_name`, `category`, `total_orders`, `total_revenue`, `average_order_value`

**`gold_revenue_by_customer`:** `customer_id`, `customer_name`, `customer_segment`, `total_orders`, `total_revenue`, `average_order_value`, `lifetime_value_actual`

**`gold_customer_segmentation`:** `customer_segment`, `customer_count`, `average_revenue`, `total_revenue`

Revenue columns: `decimal(12,2)`. `line_revenue` comes from Silver — Gold doesn't recompute it.

| Table | Expected rows |
|---|---|
| `gold_sales_by_product` | **500** (= `silver_products`) |
| `gold_customer_segmentation` | **4** |
| `gold_revenue_by_customer` | count of valid customers |

Tests: table schemas, invalid order/customer exclusion, revenue reconciliation, AOV formula, LTV = total_revenue, segment thresholds, all 500 products present.

**Suite after Gold:** 57 passed, 1 skipped (`test_gold_zero_order_products_have_zero_metrics` — all products have valid orders in generated data).

**Out of scope:** Dashboard (Phase 9), Bronze/Silver changes, new KPIs, ML segmentation, incremental Gold (overwrite only).

| Item | Value |
|---|---|
| Default catalog | `medallion_eval` |
| Gold schema | `gold` |
| Order filter | `silver_orders.is_valid_record = true` |
| Customer filter | `silver_customers.is_valid_record = true` |
| LTV | `lifetime_value_actual = total_revenue` |
| Segments | No Purchase / Low Value / Mid Value / High Value |

Invalid records stay in Silver for audit. Gold doesn't count them in business metrics.
