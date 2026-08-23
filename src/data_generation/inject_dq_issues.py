"""Controlled DQ issue injection and manifest creation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .config import (
    CUSTOMER_DUPLICATE_PAIRS,
    ISSUE_DEFINITIONS,
    ORDER_DUPLICATE_PAIRS,
)


@dataclass(frozen=True)
class ManifestEntry:
    manifest_id: str
    dataset: str
    business_key: str
    source_row_number: int
    issue_code: str
    rule_category: str
    field_name: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "dataset": self.dataset,
            "business_key": self.business_key,
            "source_row_number": self.source_row_number,
            "issue_code": self.issue_code,
            "rule_category": self.rule_category,
            "field_name": self.field_name,
            "notes": self.notes,
        }


def _issue_meta(issue_code: str) -> dict[str, str]:
    return ISSUE_DEFINITIONS[issue_code]


def inject_customer_issues(customers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[ManifestEntry]]:
    """Apply in-place and appended customer DQ issues on disjoint cohorts."""
    rows = deepcopy(customers)
    manifest: list[ManifestEntry] = []
    manifest_counter = 1

    email_indices = list(range(0, 50))
    duplicate_original_indices = list(range(9_900, 9_900 + CUSTOMER_DUPLICATE_PAIRS))

    for index in email_indices:
        rows[index]["email"] = ""
        issue = _issue_meta("CUST_EMAIL_MISSING")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["customer_id"],
                source_row_number=index + 1,
                issue_code="CUST_EMAIL_MISSING",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Injected blank email for completeness failure",
            )
        )
        manifest_counter += 1

    appended_rows: list[dict[str, Any]] = []
    for index in duplicate_original_indices:
        duplicate_row = deepcopy(rows[index])
        appended_rows.append(duplicate_row)

        issue = _issue_meta("CUST_ID_DUPLICATE")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["customer_id"],
                source_row_number=index + 1,
                issue_code="CUST_ID_DUPLICATE",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Original row in duplicate customer_id pair",
            )
        )
        manifest_counter += 1

    base_len = len(rows)
    for offset, duplicate_row in enumerate(appended_rows):
        rows.append(duplicate_row)
        issue = _issue_meta("CUST_ID_DUPLICATE")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=duplicate_row["customer_id"],
                source_row_number=base_len + offset + 1,
                issue_code="CUST_ID_DUPLICATE",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Appended duplicate customer_id row",
            )
        )
        manifest_counter += 1

    return rows, manifest


def inject_order_issues(orders: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[ManifestEntry]]:
    """Apply in-place and appended order DQ issues on disjoint cohorts."""
    rows = deepcopy(orders)
    manifest: list[ManifestEntry] = []
    manifest_counter = 1

    missing_customer_indices = list(range(0, 100))
    missing_product_indices = list(range(100, 200))
    invalid_customer_indices = list(range(200, 400))
    invalid_product_indices = list(range(400, 550))
    duplicate_original_indices = list(range(99_000, 99_000 + ORDER_DUPLICATE_PAIRS))

    for index in missing_customer_indices:
        rows[index]["customer_id"] = ""
        issue = _issue_meta("ORD_CUST_ID_MISSING")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["order_id"],
                source_row_number=index + 1,
                issue_code="ORD_CUST_ID_MISSING",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Injected blank customer_id for completeness failure",
            )
        )
        manifest_counter += 1

    for offset, index in enumerate(missing_product_indices):
        rows[index]["product_id"] = ""
        issue = _issue_meta("ORD_PROD_ID_MISSING")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["order_id"],
                source_row_number=index + 1,
                issue_code="ORD_PROD_ID_MISSING",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Injected blank product_id for completeness failure",
            )
        )
        manifest_counter += 1

    for offset, index in enumerate(invalid_customer_indices):
        orphan_id = f"CUST-INVALID-{offset + 1:03d}"
        rows[index]["customer_id"] = orphan_id
        issue = _issue_meta("ORD_CUST_ID_INVALID")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["order_id"],
                source_row_number=index + 1,
                issue_code="ORD_CUST_ID_INVALID",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes=f"Injected orphan customer_id {orphan_id}",
            )
        )
        manifest_counter += 1

    for offset, index in enumerate(invalid_product_indices):
        orphan_id = f"PROD-INVALID-{offset + 1:03d}"
        rows[index]["product_id"] = orphan_id
        issue = _issue_meta("ORD_PROD_ID_INVALID")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["order_id"],
                source_row_number=index + 1,
                issue_code="ORD_PROD_ID_INVALID",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes=f"Injected orphan product_id {orphan_id}",
            )
        )
        manifest_counter += 1

    appended_rows: list[dict[str, Any]] = []
    for index in duplicate_original_indices:
        duplicate_row = deepcopy(rows[index])
        appended_rows.append(duplicate_row)

        issue = _issue_meta("ORD_ID_DUPLICATE")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=rows[index]["order_id"],
                source_row_number=index + 1,
                issue_code="ORD_ID_DUPLICATE",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Original row in duplicate order_id pair",
            )
        )
        manifest_counter += 1

    base_len = len(rows)
    for offset, duplicate_row in enumerate(appended_rows):
        rows.append(duplicate_row)
        issue = _issue_meta("ORD_ID_DUPLICATE")
        manifest.append(
            ManifestEntry(
                manifest_id=f"DQ-{manifest_counter:04d}",
                dataset=issue["dataset"],
                business_key=duplicate_row["order_id"],
                source_row_number=base_len + offset + 1,
                issue_code="ORD_ID_DUPLICATE",
                rule_category=issue["rule_category"],
                field_name=issue["field_name"],
                notes="Appended duplicate order_id row",
            )
        )
        manifest_counter += 1

    return rows, manifest


def build_manifest(
    customer_manifest: list[ManifestEntry],
    order_manifest: list[ManifestEntry],
) -> list[ManifestEntry]:
    """Combine and re-sequence manifest IDs in deterministic order."""
    combined = customer_manifest + order_manifest
    resequenced: list[ManifestEntry] = []

    for index, entry in enumerate(combined, start=1):
        resequenced.append(
            ManifestEntry(
                manifest_id=f"DQ-{index:04d}",
                dataset=entry.dataset,
                business_key=entry.business_key,
                source_row_number=entry.source_row_number,
                issue_code=entry.issue_code,
                rule_category=entry.rule_category,
                field_name=entry.field_name,
                notes=entry.notes,
            )
        )

    return resequenced
