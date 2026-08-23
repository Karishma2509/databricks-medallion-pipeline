"""End-to-end data generation pipeline for Phase 5."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import (
    FINAL_CUSTOMER_COUNT,
    FINAL_ORDER_COUNT,
    FINAL_PRODUCT_COUNT,
    ISSUE_DEFINITIONS,
    MANIFEST_PATH,
    RAW_DATA_DIR,
)
from .generators import generate_customers, generate_orders, generate_products
from .inject_dq_issues import (
    ManifestEntry,
    build_manifest,
    inject_customer_issues,
    inject_order_issues,
)
from .io import write_all_outputs


@dataclass(frozen=True)
class GenerationResult:
    customers: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    products: list[dict[str, Any]]
    manifest: list[ManifestEntry]
    output_paths: dict[str, Path]


def generate_datasets(
    raw_dir: Path | None = None,
    manifest_path: Path | None = None,
    write_outputs: bool = True,
) -> GenerationResult:
    """Generate base datasets, inject DQ issues, and optionally write CSV outputs."""
    products = generate_products()
    customers = generate_customers()
    orders = generate_orders(customers, products)

    customers_final, customer_manifest = inject_customer_issues(customers)
    orders_final, order_manifest = inject_order_issues(orders)
    manifest = build_manifest(customer_manifest, order_manifest)

    _validate_generation(customers_final, orders_final, products, manifest)

    output_paths: dict[str, Path] = {}
    if write_outputs:
        output_paths = write_all_outputs(
            customers_final,
            orders_final,
            products,
            manifest,
            raw_dir=raw_dir,
            manifest_path=manifest_path,
        )

    return GenerationResult(
        customers=customers_final,
        orders=orders_final,
        products=products,
        manifest=manifest,
        output_paths=output_paths,
    )


def _validate_generation(
    customers: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    products: list[dict[str, Any]],
    manifest: list[ManifestEntry],
) -> None:
    if len(customers) != FINAL_CUSTOMER_COUNT:
        raise ValueError(f"Expected {FINAL_CUSTOMER_COUNT} customers, got {len(customers)}")
    if len(orders) != FINAL_ORDER_COUNT:
        raise ValueError(f"Expected {FINAL_ORDER_COUNT} orders, got {len(orders)}")
    if len(products) != FINAL_PRODUCT_COUNT:
        raise ValueError(f"Expected {FINAL_PRODUCT_COUNT} products, got {len(products)}")
    if len(manifest) != 700:
        raise ValueError(f"Expected 700 manifest entries, got {len(manifest)}")

    counts: dict[str, int] = {}
    for entry in manifest:
        counts[entry.issue_code] = counts.get(entry.issue_code, 0) + 1

    for issue_code, definition in ISSUE_DEFINITIONS.items():
        expected = definition["count"]
        actual = counts.get(issue_code, 0)
        if actual != expected:
            raise ValueError(
                f"Expected {expected} manifest rows for {issue_code}, got {actual}"
            )


def main() -> None:
    result = generate_datasets(
        raw_dir=RAW_DATA_DIR,
        manifest_path=MANIFEST_PATH,
        write_outputs=True,
    )
    print("Data generation complete.")
    print(f"Customers: {len(result.customers)} rows -> {result.output_paths['customers']}")
    print(f"Orders: {len(result.orders)} rows -> {result.output_paths['orders']}")
    print(f"Products: {len(result.products)} rows -> {result.output_paths['products']}")
    print(f"Manifest: {len(result.manifest)} issues -> {result.output_paths['manifest']}")


if __name__ == "__main__":
    main()
