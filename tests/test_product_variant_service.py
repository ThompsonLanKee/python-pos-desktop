
from uuid import uuid4

from src.core.database import Database
from src.models import Category, Product, ProductVariant, Color, Size
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ColorRepository,
    SizeRepository,
    InventoryRepository,
)
from src.services.product_service import ProductService
from src.services.product_variant_service import ProductVariantService


def run_tests():

    database = Database()
    database.initialize()

    category_repo = CategoryRepository(database)
    product_repo = ProductRepository(database)
    color_repo = ColorRepository(database)
    size_repo = SizeRepository(database)
    inventory_repo = InventoryRepository(database)

    product_service = ProductService(database)
    variant_service = ProductVariantService(database)

    suffix = uuid4().hex[:8]

    category_id = category_repo.create(
        Category(category_name=f"Variant Service {suffix}")
    )

    product_id = product_service.create_product(
        Product(
            product_name=f"Test Product {suffix}",
            category_id=category_id
        ),
        [
            {
                "sku": f"BASE-{suffix}",
                "color_id": None,
                "size_id": None,
                "cost_price": 100,
                "selling_price": 200
            }
        ]
    )

    color_id = color_repo.create(
        Color(color_name=f"Blue {suffix}")
    )

    size_id = size_repo.create(
        Size(size_name=f"XL-{suffix}")
    )

    # Add variant.
    variant = ProductVariant(
        product_id=product_id,
        color_id=color_id,
        size_id=size_id,
        sku=f"NEW-{suffix}",
        cost_price=300,
        selling_price=500
    )

    variant_id = variant_service.add_variant(variant)

    print("Add variant: PASSED")

    # Verify automatic inventory.
    inventory = inventory_repo.get_by_variant(variant_id)

    assert inventory is not None
    assert inventory["quantity_on_hand"] == 0

    print("Automatic inventory initialization: PASSED")

    # Retrieve by ID.
    assert variant_service.get_variant_by_id(variant_id)

    print("Retrieve variant by ID: PASSED")

    # Retrieve by SKU.
    assert variant_service.get_variant_by_sku(
        f"NEW-{suffix}"
    )

    print("Retrieve variant by SKU: PASSED")

    # Retrieve by product.
    variants = variant_service.get_variants_by_product(
        product_id
    )

    assert len(variants) == 2

    print("Retrieve variants by product: PASSED")

    # Update variant.
    variant.variant_id = variant_id
    variant.selling_price = 600

    assert variant_service.update_variant(variant)

    updated = variant_service.get_variant_by_id(variant_id)

    assert updated.selling_price == 600

    print("Update variant: PASSED")

    # Duplicate SKU prevention.
    duplicate = ProductVariant(
        product_id=product_id,
        color_id=None,
        size_id=None,
        sku=f"NEW-{suffix}",
        cost_price=100,
        selling_price=200
    )

    try:
        variant_service.add_variant(duplicate)

    except ValueError:
        print("Duplicate SKU prevention: PASSED")

    else:
        raise AssertionError("Duplicate SKU was accepted.")

    # Deactivate variant.
    assert variant_service.set_variant_active(
        variant_id,
        False
    )

    print("Variant deactivation: PASSED")

    print("\nAll ProductVariantService tests passed!")


if __name__ == "__main__":
    run_tests()
