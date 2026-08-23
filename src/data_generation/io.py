"""CSV and manifest I/O helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

from .config import (
    CUSTOMER_COLUMNS,
    MANIFEST_PATH,
    ORDER_COLUMNS,
    PRODUCT_COLUMNS,
    RAW_DATA_DIR,
)
from .inject_dq_issues import ManifestEntry


MANIFEST_COLUMNS = [
    "manifest_id",
    "dataset",
    "business_key",
    "source_row_number",
    "issue_code",
    "rule_category",
    "field_name",
    "notes",
]


def write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.as_dict())


def write_all_outputs(
    customers: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    products: list[dict[str, Any]],
    manifest: list[ManifestEntry],
    raw_dir: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Path]:
    raw_dir = raw_dir or RAW_DATA_DIR
    manifest_path = manifest_path or MANIFEST_PATH

    customer_path = raw_dir / "customers.csv"
    order_path = raw_dir / "orders.csv"
    product_path = raw_dir / "products.csv"

    write_csv(customer_path, CUSTOMER_COLUMNS, customers)
    write_csv(order_path, ORDER_COLUMNS, orders)
    write_csv(product_path, PRODUCT_COLUMNS, products)
    write_manifest(manifest_path, manifest)

    return {
        "customers": customer_path,
        "orders": order_path,
        "products": product_path,
        "manifest": manifest_path,
    }
