
from uuid import uuid4

from src.core.database import Database

from src.models import (
    Category,
    Product,
    Color,
    Size,
    ProductVariant
)

from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ColorRepository,
    SizeRepository,
    ProductVariantRepository,
    InventoryRepository
)


def test_variant_repositories():

    database = Database()

    category_repo = CategoryRepository(database)
    product_repo = ProductRepository(database)
    color_repo = ColorRepository(database)
    size_repo = SizeRepository(database)
    variant_repo = ProductVariantRepository(database)
    inventory_repo = InventoryRepository(database)

    suffix = uuid4().hex[:8]

    # ======================================
    # CATEGORY
    # ======================================

    category_id = category_repo.create(
        Category(
            category_name=f"Clothing {suffix}"
        )
    )

    print("Category creation: PASSED")

    # ======================================
    # PRODUCT
    # ======================================

    product_id = product_repo.create(
        Product(
            product_name=f"Cotton T-Shirt {suffix}",
            category_id=category_id,
            brand="Lankee"
        )
    )

    print("Product creation: PASSED")

    # ======================================
    # COLOR
    # ======================================

    color_id = color_repo.create(
        Color(
            color_name=f"Black {suffix}",
            hex_code="#000000"
        )
    )

    print("Color creation: PASSED")

    # ======================================
    # SIZE
    # ======================================

    size_id = size_repo.create(
        Size(
            size_name=f"M-{suffix}",
            sort_order=2
        )
    )

    print("Size creation: PASSED")

    # ======================================
    # PRODUCT VARIANT
    # ======================================

    sku = f"TS-BLK-M-{suffix}".upper()

    variant_id = variant_repo.create(
        ProductVariant(
            product_id=product_id,
            color_id=color_id,
            size_id=size_id,
            sku=sku,
            cost_price=8000,
            selling_price=12000
        )
    )

    saved_variant = variant_repo.get_by_id(variant_id)

    assert saved_variant is not None
    assert saved_variant.sku == sku

    print("Product variant creation: PASSED")

    # ======================================
    # INVENTORY
    # ======================================

    inventory_repo.create(variant_id)

    inventory = inventory_repo.get_by_variant(variant_id)

    assert inventory is not None
    assert inventory["quantity_on_hand"] == 0

    print("Inventory initialization: PASSED")

    # ======================================
    # STOCK ADJUSTMENT
    # ======================================

    assert inventory_repo.adjust_quantity(
        variant_id, 20
    )

    inventory = inventory_repo.get_by_variant(variant_id)

    assert inventory["quantity_on_hand"] == 20

    print("Stock increase: PASSED")

    # ======================================
    # STOCK VALIDATION
    # ======================================

    assert not inventory_repo.adjust_quantity(
        variant_id, -25
    )

    inventory = inventory_repo.get_by_variant(variant_id)

    assert inventory["quantity_on_hand"] == 20

    print("Negative stock prevention: PASSED")

    print("\nAll variant repository tests passed!")


if __name__ == "__main__":
    test_variant_repositories()
