import json
import sys
from collections import Counter
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data_generation.config import (  # noqa: E402
    CUSTOMER_COLUMNS,
    FINAL_CUSTOMER_COUNT,
    FINAL_ORDER_COUNT,
    FINAL_PRODUCT_COUNT,
    ISSUE_DEFINITIONS,
    ORDER_COLUMNS,
    PRODUCT_COLUMNS,
)
from data_generation.generators import (  # noqa: E402
    generate_customers,
    generate_orders,
    generate_products,
)
from data_generation.io import read_csv  # noqa: E402
from data_generation.run_generator import generate_datasets  # noqa: E402


@pytest.fixture
def expected_issue_counts() -> dict[str, int]:
    fixture_path = PROJECT_ROOT / "tests" / "fixtures" / "manifest_expected_counts.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


@pytest.fixture
def generated_outputs(tmp_path):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifests" / "dq_injection_manifest.csv"
    return generate_datasets(
        raw_dir=raw_dir,
        manifest_path=manifest_path,
        write_outputs=True,
    )


def test_deterministic_generation(tmp_path):
    raw_dir = tmp_path / "raw"
    manifest_path = tmp_path / "manifests" / "dq_injection_manifest.csv"

    first = generate_datasets(raw_dir=raw_dir, manifest_path=manifest_path, write_outputs=True)
    second = generate_datasets(raw_dir=raw_dir, manifest_path=manifest_path, write_outputs=True)

    assert first.customers == second.customers
    assert first.orders == second.orders
    assert first.products == second.products
    assert [entry.as_dict() for entry in first.manifest] == [
        entry.as_dict() for entry in second.manifest
    ]


def test_final_row_counts(generated_outputs):
    result = generated_outputs
    assert len(result.customers) == FINAL_CUSTOMER_COUNT
    assert len(result.orders) == FINAL_ORDER_COUNT
    assert len(result.products) == FINAL_PRODUCT_COUNT


def test_csv_schemas(generated_outputs):
    paths = generated_outputs.output_paths
    customers = read_csv(paths["customers"])
    orders = read_csv(paths["orders"])
    products = read_csv(paths["products"])

    assert list(customers[0].keys()) == CUSTOMER_COLUMNS
    assert list(orders[0].keys()) == ORDER_COLUMNS
    assert list(products[0].keys()) == PRODUCT_COLUMNS


def test_base_id_uniqueness_before_injection():
    products = generate_products()
    customers = generate_customers()
    orders = generate_orders(customers, products)

    customer_ids = [row["customer_id"] for row in customers]
    order_ids = [row["order_id"] for row in orders]
    product_ids = [row["product_id"] for row in products]

    assert len(customer_ids) == len(set(customer_ids))
    assert len(order_ids) == len(set(order_ids))
    assert len(product_ids) == len(set(product_ids))


def test_clean_baseline_references_exist():
    products = generate_products()
    customers = generate_customers()
    orders = generate_orders(customers, products)

    customer_ids = {row["customer_id"] for row in customers}
    product_ids = {row["product_id"] for row in products}

    assert all(order["customer_id"] in customer_ids for order in orders)
    assert all(order["product_id"] in product_ids for order in orders)


def test_manifest_has_exactly_700_entries(generated_outputs, expected_issue_counts):
    manifest = generated_outputs.manifest
    assert len(manifest) == 700
    assert sum(expected_issue_counts.values()) == 700


def test_manifest_issue_code_counts(generated_outputs, expected_issue_counts):
    counts = Counter(entry.issue_code for entry in generated_outputs.manifest)
    for issue_code, expected_count in expected_issue_counts.items():
        assert counts[issue_code] == expected_count
        assert counts[issue_code] == ISSUE_DEFINITIONS[issue_code]["count"]


def test_manifest_traceability_to_csv(generated_outputs):
    paths = generated_outputs.output_paths
    customers = read_csv(paths["customers"])
    orders = read_csv(paths["orders"])

    for entry in generated_outputs.manifest:
        row_number = int(entry.source_row_number)
        if entry.dataset == "customers":
            row = customers[row_number - 1]
            assert row["customer_id"] == entry.business_key
        elif entry.dataset == "orders":
            row = orders[row_number - 1]
            assert row["order_id"] == entry.business_key


def test_injected_issue_types_present(generated_outputs):
    customers = generated_outputs.customers
    orders = generated_outputs.orders

    blank_emails = sum(1 for row in customers if row["email"].strip() == "")
    assert blank_emails == 50

    customer_id_counts = Counter(row["customer_id"] for row in customers)
    duplicate_customer_ids = sum(1 for count in customer_id_counts.values() if count > 1)
    assert duplicate_customer_ids == 15

    blank_customer_ids = sum(1 for row in orders if row["customer_id"].strip() == "")
    blank_product_ids = sum(1 for row in orders if row["product_id"].strip() == "")
    assert blank_customer_ids == 100
    assert blank_product_ids == 100

    invalid_customer_refs = sum(
        1 for row in orders if row["customer_id"].startswith("CUST-INVALID-")
    )
    invalid_product_refs = sum(
        1 for row in orders if row["product_id"].startswith("PROD-INVALID-")
    )
    assert invalid_customer_refs == 200
    assert invalid_product_refs == 150

    order_id_counts = Counter(row["order_id"] for row in orders)
    duplicate_order_ids = sum(1 for count in order_id_counts.values() if count > 1)
    assert duplicate_order_ids == 35


def test_disjoint_issue_cohorts(generated_outputs):
    """Initial 700-issue plan should not overlap issue categories on the same row."""
    orders = generated_outputs.orders

    for index, row in enumerate(orders):
        flags = [
            row["customer_id"].strip() == "",
            row["product_id"].strip() == "",
            row["customer_id"].startswith("CUST-INVALID-"),
            row["product_id"].startswith("PROD-INVALID-"),
        ]
        assert sum(flags) <= 1, f"Overlapping order issues at row {index + 1}"

    customers = generated_outputs.customers
    for index, row in enumerate(customers):
        if row["email"].strip() == "":
            assert index < 50
