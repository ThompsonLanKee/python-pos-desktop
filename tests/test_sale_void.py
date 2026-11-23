
from uuid import uuid4

from src.core.database import Database
from src.models import Category, Product, ProductVariant, Sale
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    InventoryRepository,
    InventoryTransactionRepository,
    SaleRepository,
)
from src.services.sale_service import SaleService


def run_tests():

    database = Database()
    database.initialize()

    category_repo = CategoryRepository(database)
    product_repo = ProductRepository(database)
    variant_repo = ProductVariantRepository(database)
    inventory_repo = InventoryRepository(database)
    transaction_repo = InventoryTransactionRepository(database)
    sale_repo = SaleRepository(database)

    sale_service = SaleService(database)

    suffix = uuid4().hex[:10]

    print("\nStarting Sale Void tests...\n")

    # 1. Prepare product and inventory.
    category_id = category_repo.create(
        Category(category_name=f"Void Category {suffix}")
    )

    product_id = product_repo.create(
        Product(
            product_name=f"Void Product {suffix}",
            category_id=category_id
        )
    )

    variant_id = variant_repo.create(
        ProductVariant(
            product_id=product_id,
            color_id=None,
            size_id=None,
            sku=f"VOID-{suffix}",
            barcode=None,
            cost_price=500,
            selling_price=1000
        )
    )

    inventory_repo.create(variant_id)
    inventory_repo.adjust_quantity(variant_id, 10)

    # 2. Create an unpaid sale.
    sale_number = f"VOID-SALE-{suffix}"

    sale = Sale(
        sale_number=sale_number,
        subtotal=2000,
        discount_amount=0,
        tax_amount=0,
        total_amount=2000
    )

    result = sale_service.create_sale(
        sale=sale,
        items=[
            {
                "variant_id": variant_id,
                "quantity": 2
            }
        ]
    )

    sale_id = result["sale_id"]

    # Stock should now be 8.
    assert (
        inventory_repo.get_by_variant(variant_id)["quantity_on_hand"]
        == 8
    )

    print("Sale creation and stock deduction: PASSED")

    # 3. Void sale.
    assert sale_service.void_sale(sale_id) is True

    print("Sale void operation: PASSED")

    # 4. Verify sale status.
    voided_sale = sale_repo.get_by_id(sale_id)

    assert voided_sale.sale_status == "VOIDED"

    print("Sale status update: PASSED")

    # 5. Verify stock restoration.
    inventory = inventory_repo.get_by_variant(variant_id)

    assert inventory["quantity_on_hand"] == 10

    print("Inventory restoration: PASSED")

    # 6. Verify inventory transaction history.
    history = transaction_repo.get_by_variant(variant_id)

    void_movements = [
        movement
        for movement in history
        if movement.reference_type == "SALE_VOID"
        and movement.reference_id == sale_id
    ]

    assert len(void_movements) == 1
    assert void_movements[0].quantity_change == 2
    assert void_movements[0].quantity_after == 10

    print("Sale void inventory history: PASSED")

    # 7. Prevent repeated voiding.
    try:
        sale_service.void_sale(sale_id)

    except ValueError:
        print("Repeated void prevention: PASSED")

    else:
        raise AssertionError(
            "A voided sale was allowed to be voided again."
        )

    # 8. Verify stock was not restored twice.
    inventory = inventory_repo.get_by_variant(variant_id)

    assert inventory["quantity_on_hand"] == 10

    print("Duplicate stock restoration prevention: PASSED")

    print("\nAll Sale Void tests passed!")


if __name__ == "__main__":
    run_tests()
