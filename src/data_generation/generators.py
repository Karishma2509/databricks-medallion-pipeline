"""Deterministic base dataset generators."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from .config import (
    BASE_CUSTOMER_COUNT,
    BASE_ORDER_COUNT,
    BASE_PRODUCT_COUNT,
    COUNTRIES,
    GENERATION_SEED,
    PRODUCT_CATEGORIES,
    SIGNUP_CHANNELS,
)


def _customer_id(index: int) -> str:
    return f"CUST-{index:05d}"


def _order_id(index: int) -> str:
    return f"ORD-{index:07d}"


def _product_id(index: int) -> str:
    return f"PROD-{index:03d}"


def generate_products() -> list[dict[str, Any]]:
    rng = random.Random(GENERATION_SEED)
    products: list[dict[str, Any]] = []

    for index in range(1, BASE_PRODUCT_COUNT + 1):
        category = PRODUCT_CATEGORIES[(index - 1) % len(PRODUCT_CATEGORIES)]
        list_price = round(rng.uniform(5.0, 500.0), 2)
        products.append(
            {
                "product_id": _product_id(index),
                "product_name": f"{category} Product {index}",
                "category": category,
                "list_price": f"{list_price:.2f}",
                "is_active": "true" if index % 17 != 0 else "false",
            }
        )

    return products


def generate_customers() -> list[dict[str, Any]]:
    rng = random.Random(GENERATION_SEED + 1)
    start_date = date(2018, 1, 1)
    customers: list[dict[str, Any]] = []

    for index in range(1, BASE_CUSTOMER_COUNT + 1):
        registration_date = start_date + timedelta(days=rng.randint(0, 2_500))
        customers.append(
            {
                "customer_id": _customer_id(index),
                "customer_name": f"Customer {index}",
                "email": f"customer{index}@example.com",
                "registration_date": registration_date.isoformat(),
                "country": COUNTRIES[(index - 1) % len(COUNTRIES)],
                "signup_channel": SIGNUP_CHANNELS[(index - 1) % len(SIGNUP_CHANNELS)],
            }
        )

    return customers


def generate_orders(
    customers: list[dict[str, Any]],
    products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rng = random.Random(GENERATION_SEED + 2)
    start_date = date(2020, 1, 1)
    customer_ids = [row["customer_id"] for row in customers]
    product_ids = [row["product_id"] for row in products]
    product_prices = {row["product_id"]: float(row["list_price"]) for row in products}
    orders: list[dict[str, Any]] = []

    for index in range(1, BASE_ORDER_COUNT + 1):
        customer_id = customer_ids[rng.randrange(len(customer_ids))]
        product_id = product_ids[rng.randrange(len(product_ids))]
        quantity = rng.randint(1, 5)
        base_price = product_prices[product_id]
        unit_price = round(base_price * rng.uniform(0.9, 1.1), 2)
        order_date = start_date + timedelta(days=rng.randint(0, 1_800))

        orders.append(
            {
                "order_id": _order_id(index),
                "customer_id": customer_id,
                "product_id": product_id,
                "order_date": order_date.isoformat(),
                "quantity": str(quantity),
                "unit_price": f"{unit_price:.2f}",
            }
        )

    return orders
