
from uuid import uuid4

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

    # ==========================================
    # CREATE TEST PRODUCT AND VARIANT
    # ==========================================

    category_id = category_repo.create(
        Category(
            category_name=f"Inventory Test {suffix}"
        )
    )

    product_id = product_service.create_product(
        Product(
            product_name=f"Inventory Product {suffix}",
            category_id=category_id
        ),
        [
            {
                "sku": f"INVENTORY-{suffix}",
                "color_id": None,
                "size_id": None,
                "cost_price": 1000,
                "selling_price": 1500
            }
        ]
    )

    details = product_service.get_product_details(product_id)

    variant_id = details["variants"][0]["variant_id"]

    # ==========================================
    # TEST INITIAL INVENTORY
    # ==========================================

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory is not None
    assert inventory["quantity_on_hand"] == 0

    print("Initial inventory retrieval: PASSED")

    # ==========================================
    # TEST RECEIVE STOCK
    # ==========================================

    assert inventory_service.receive_stock(
        variant_id,
        20
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 20

    print("Stock receiving: PASSED")

    # ==========================================
    # TEST ISSUE STOCK
    # ==========================================

    assert inventory_service.issue_stock(
        variant_id,
        5
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 15

    print("Stock issuing: PASSED")

    # ==========================================
    # TEST INSUFFICIENT STOCK
    # ==========================================

    assert not inventory_service.issue_stock(
        variant_id,
        20
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 15

    print("Negative stock prevention: PASSED")

    # ==========================================
    # TEST MANUAL ADJUSTMENT
    # ==========================================

    assert inventory_service.adjust_stock(
        variant_id,
        10
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 25

    print("Manual stock adjustment: PASSED")

    # ==========================================
    # TEST SET STOCK QUANTITY
    # ==========================================

    assert inventory_service.set_stock_quantity(
        variant_id,
        30
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["quantity_on_hand"] == 30

    print("Set stock quantity: PASSED")

    # ==========================================
    # TEST REORDER LEVEL
    # ==========================================

    assert inventory_service.set_reorder_level(
        variant_id,
        10
    )

    inventory = inventory_service.get_inventory(variant_id)

    assert inventory["reorder_level"] == 10

    print("Reorder level update: PASSED")

    # ==========================================
    # TEST LOW STOCK
    # ==========================================

    assert inventory_service.set_stock_quantity(
        variant_id,
        5
    )

    low_stock = inventory_service.get_low_stock()

    assert any(
        item["variant_id"] == variant_id
        for item in low_stock
    )

    print("Low-stock detection: PASSED")

    # ==========================================
    # TEST INVALID QUANTITY
    # ==========================================

    try:
        inventory_service.receive_stock(
            variant_id,
            -5
        )

    except ValueError:
        print("Invalid quantity prevention: PASSED")

    else:
        raise AssertionError(
            "Negative receiving quantity was accepted."
        )

    print("\nAll InventoryService tests passed!")


if __name__ == "__main__":
    run_tests()
