"""Generation constants aligned with approved Phase 4 design."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "dq_injection_manifest.csv"

GENERATION_SEED = 42

BASE_CUSTOMER_COUNT = 10_000
BASE_ORDER_COUNT = 100_000
BASE_PRODUCT_COUNT = 500

FINAL_CUSTOMER_COUNT = 10_015
FINAL_ORDER_COUNT = 100_035
FINAL_PRODUCT_COUNT = 500

CUSTOMER_DUPLICATE_PAIRS = 15
ORDER_DUPLICATE_PAIRS = 35

CUSTOMER_COLUMNS = [
    "customer_id",
    "customer_name",
    "email",
    "registration_date",
    "country",
    "signup_channel",
]

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "unit_price",
]

PRODUCT_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "list_price",
    "is_active",
]

ISSUE_DEFINITIONS = {
    "CUST_EMAIL_MISSING": {
        "dataset": "customers",
        "rule_category": "completeness",
        "field_name": "email",
        "count": 50,
    },
    "CUST_ID_DUPLICATE": {
        "dataset": "customers",
        "rule_category": "uniqueness",
        "field_name": "customer_id",
        "count": 30,
    },
    "ORD_CUST_ID_MISSING": {
        "dataset": "orders",
        "rule_category": "completeness",
        "field_name": "customer_id",
        "count": 100,
    },
    "ORD_PROD_ID_MISSING": {
        "dataset": "orders",
        "rule_category": "completeness",
        "field_name": "product_id",
        "count": 100,
    },
    "ORD_ID_DUPLICATE": {
        "dataset": "orders",
        "rule_category": "uniqueness",
        "field_name": "order_id",
        "count": 70,
    },
    "ORD_CUST_ID_INVALID": {
        "dataset": "orders",
        "rule_category": "referential_integrity",
        "field_name": "customer_id",
        "count": 200,
    },
    "ORD_PROD_ID_INVALID": {
        "dataset": "orders",
        "rule_category": "referential_integrity",
        "field_name": "product_id",
        "count": 150,
    },
}

SIGNUP_CHANNELS = ("web", "mobile", "referral", "partner")
COUNTRIES = ("US", "UK", "CA", "DE", "FR", "AU", "IN")
PRODUCT_CATEGORIES = (
    "Electronics",
    "Clothing",
    "Home",
    "Sports",
    "Books",
    "Beauty",
    "Toys",
    "Garden",
)
