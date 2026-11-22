
import sqlite3
from uuid import uuid4
from unittest.mock import patch

from src.core.database import Database
from src.models import Category, Product
from src.repositories import CategoryRepository
from src.services.product_service import ProductService
from src.services.inventory_service import InventoryService


def run_tests():

    database = Database()
    database.initialize()

    category_repo = CategoryRepository(database)
    product_service = ProductService(database)
    inventory_service = InventoryService(database)

    suffix = uuid4().hex[:8]

    category_id = category_repo.create(
        Category(category_name=f"History Test {suffix}")
    )

    product_id = product_service.create_product(
        Product(
            product_name=f"History Product {suffix}",
            category_id=category_id
        ),
        [
            {
                "sku": f"HISTORY-{suffix}",
                "color_id": None,
                "size_id": None,
                "cost_price": 100,
                "selling_price": 200
            }
        ]
    )

    details = product_service.get_product_details(product_id)
    variant_id = details["variants"][0]["variant_id"]

    # Receive stock: 20
    assert inventory_service.receive_stock(
        variant_id,
        20,
        notes="Initial goods receipt"
    )

    # Issue stock: 5
    assert inventory_service.issue_stock(
        variant_id,
        5,
        notes="Test sale"
    )

    # Manual adjustment: +10
    assert inventory_service.adjust_stock(
        variant_id,
        10,
        notes="Stock count correction"
    )

    # Damage: -2
    assert inventory_service.record_damage(
        variant_id,
        2,
        notes="Damaged goods"
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 23

    print("Stock balance calculation: PASSED")

    history = inventory_service.get_transaction_history(
        variant_id
    )

    assert len(history) == 4

    expected = [
        ("DAMAGE", -2, 23),
        ("ADJUSTMENT_IN", 10, 25),
        ("SALE", -5, 15),
        ("PURCHASE", 20, 20),
    ]

    actual = [
        (
            item.transaction_type,
            item.quantity_change,
            item.quantity_after
        )
        for item in history
    ]

    assert actual == expected

    print("Transaction history retrieval: PASSED")
    print("Transaction quantity balances: PASSED")

    # Insufficient stock must not create a transaction.
    history_count = len(history)

    assert not inventory_service.issue_stock(
        variant_id,
        100
    )

    updated_history = inventory_service.get_transaction_history(
        variant_id
    )

    assert len(updated_history) == history_count

    print("Insufficient stock history prevention: PASSED")

    # A history write failure must also roll back the balance update.
    try:
        with patch.object(
            inventory_service.transaction_repository,
            "create",
            side_effect=sqlite3.IntegrityError("forced history failure")
        ):
            inventory_service.receive_stock(variant_id, 1)

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Expected history failure to abort the stock movement."
        )

    inventory = inventory_service.get_inventory(variant_id)
    history_after_failure = inventory_service.get_transaction_history(
        variant_id
    )

    assert inventory["quantity_on_hand"] == 23
    assert len(history_after_failure) == history_count

    print("Atomic balance and history rollback: PASSED")

    # Set stock quantity should also create a movement.
    assert inventory_service.set_stock_quantity(
        variant_id,
        30,
        notes="Physical stock count"
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 30

    latest_history = inventory_service.get_transaction_history(
        variant_id
    )

    assert latest_history[0].quantity_change == 7
    assert latest_history[0].transaction_type == "ADJUSTMENT_IN"

    print("Stock count correction history: PASSED")

    print("\nAll inventory transaction tests passed!")


if __name__ == "__main__":
    run_tests()
