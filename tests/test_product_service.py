
from uuid import uuid4
from contextlib import closing

from src.core.database import Database
from src.models import Category, Product, Color, Size, ProductVariant
from src.repositories import (
    CategoryRepository,
    ProductRepository,
    ColorRepository,
    SizeRepository,
    ProductVariantRepository,
    InventoryRepository,
)
from src.services.product_service import ProductService


def run_tests():
    database = Database()
    database.initialize()

    category_repo = CategoryRepository(database)
    product_repo = ProductRepository(database)
    color_repo = ColorRepository(database)
    size_repo = SizeRepository(database)
    variant_repo = ProductVariantRepository(database)
    inventory_repo = InventoryRepository(database)

    product_service = ProductService(database)

    suffix = uuid4().hex[:8]

    # ==========================================
    # TEST DATA
    # ==========================================

    category_id = category_repo.create(
        Category(category_name=f"Service Test Category {suffix}")
    )

    color_black_id = color_repo.create(
        Color(color_name=f"Black {suffix}")
    )

    color_white_id = color_repo.create(
        Color(color_name=f"White {suffix}")
    )

    size_m_id = size_repo.create(
        Size(size_name=f"M-{suffix}")
    )

    size_l_id = size_repo.create(
        Size(size_name=f"L-{suffix}")
    )

    # ==========================================
    # TEST 1: SIMPLE PRODUCT
    # ==========================================

    simple_product = Product(
        product_name=f"Notebook {suffix}",
        description="Simple product test",
        category_id=category_id,
        brand="Test Brand"
    )

    simple_variants = [
        {
            "sku": f"NOTEBOOK-{suffix}",
            "color_id": None,
            "size_id": None,
            "cost_price": 1000,
            "selling_price": 1500
        }
    ]

    simple_product_id = product_service.create_product(
        simple_product,
        simple_variants
    )

    simple_saved = product_repo.get_by_id(simple_product_id)
    simple_saved_variants = variant_repo.get_by_product(
        simple_product_id
    )

    assert simple_saved is not None
    assert len(simple_saved_variants) == 1

    simple_inventory = inventory_repo.get_by_variant(
        simple_saved_variants[0].variant_id
    )

    assert simple_inventory is not None
    assert simple_inventory["quantity_on_hand"] == 0

    print("Simple product creation: PASSED")

    # ==========================================
    # TEST 2: CLOTHING WITH MULTIPLE VARIANTS
    # ==========================================

    clothing_product = Product(
        product_name=f"T-Shirt {suffix}",
        description="Multiple variant test",
        category_id=category_id,
        brand="Test Clothing"
    )

    clothing_variants = [
        {
            "sku": f"TSHIRT-BLK-M-{suffix}",
            "color_id": color_black_id,
            "size_id": size_m_id,
            "cost_price": 5000,
            "selling_price": 9000
        },
        {
            "sku": f"TSHIRT-BLK-L-{suffix}",
            "color_id": color_black_id,
            "size_id": size_l_id,
            "cost_price": 5000,
            "selling_price": 9000
        },
        {
            "sku": f"TSHIRT-WHT-M-{suffix}",
            "color_id": color_white_id,
            "size_id": size_m_id,
            "cost_price": 5000,
            "selling_price": 9000
        }
    ]

    clothing_product_id = product_service.create_product(
        clothing_product,
        clothing_variants
    )

    saved_clothing_variants = variant_repo.get_by_product(
        clothing_product_id
    )

    assert len(saved_clothing_variants) == 3

    for variant in saved_clothing_variants:
        inventory = inventory_repo.get_by_variant(
            variant.variant_id
        )

        assert inventory is not None
        assert inventory["quantity_on_hand"] == 0

    print("Multiple clothing variants: PASSED")
    print("Automatic inventory initialization: PASSED")

    # ==========================================
    # TEST 3: REJECT DUPLICATE SKU
    # ==========================================

    duplicate_sku_product = Product(
        product_name=f"Duplicate SKU Test {suffix}",
        category_id=category_id
    )

    duplicate_sku_variants = [
        {
            "sku": f"DUPLICATE-{suffix}",
            "color_id": None,
            "size_id": None,
            "cost_price": 100,
            "selling_price": 200
        },
        {
            "sku": f"duplicate-{suffix}",
            "color_id": 1,
            "size_id": 1,
            "cost_price": 100,
            "selling_price": 200
        }
    ]

    try:
        product_service.create_product(
            duplicate_sku_product,
            duplicate_sku_variants
        )

    except ValueError:
        print("Duplicate SKU prevention: PASSED")

    else:
        raise AssertionError("Duplicate SKU was accepted.")

    # ==========================================
    # TEST 4: REJECT INVALID CATEGORY
    # ==========================================

    invalid_product = Product(
        product_name=f"Invalid Category Test {suffix}",
        category_id=999999999
    )

    try:
        product_service.create_product(
            invalid_product,
            [
                {
                    "sku": f"INVALID-CATEGORY-{suffix}",
                    "color_id": None,
                    "size_id": None,
                    "cost_price": 100,
                    "selling_price": 200
                }
            ]
        )

    except ValueError:
        print("Invalid category prevention: PASSED")

    else:
        raise AssertionError("Invalid category was accepted.")

    # ==========================================
    # TEST 5: VERIFY FULL TRANSACTION ROLLBACK
    # ==========================================

    # Create an existing variant with a unique barcode.
    # The service will encounter this barcode on its
    # second variant, after inserting the first one.

    rollback_base_product = Product(
        product_name=f"Rollback Base Product {suffix}",
        category_id=category_id
    )

    rollback_base_product_id = product_repo.create(
        rollback_base_product
    )

    existing_variant = ProductVariant(
        product_id=rollback_base_product_id,
        color_id=None,
        size_id=None,
        sku=f"ROLLBACK-BASE-{suffix}",
        barcode=f"EXISTING-BARCODE-{suffix}",
        cost_price=100,
        selling_price=200
    )

    existing_variant_id = variant_repo.create(existing_variant)
    inventory_repo.create(existing_variant_id)

    rollback_product = Product(
        product_name=f"Rollback Product {suffix}",
        category_id=category_id
    )

    rollback_variants = [
        {
            "sku": f"ROLLBACK-FIRST-{suffix}",
            "color_id": None,
            "size_id": None,
            "barcode": f"NEW-BARCODE-{suffix}",
            "cost_price": 100,
            "selling_price": 200
        },
        {
            "sku": f"ROLLBACK-SECOND-{suffix}",
            "color_id": None,
            "size_id": None,
            "barcode": f"EXISTING-BARCODE-{suffix}",
            "cost_price": 100,
            "selling_price": 200
        }
    ]

    try:
        product_service.create_product(
            rollback_product,
            rollback_variants
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Expected duplicate barcode to fail."
        )

    with closing(database.connect()) as connection:

        saved_product = connection.execute(
            """
            SELECT product_id
            FROM products
            WHERE product_name = ?
            """,
            (rollback_product.product_name,)
        ).fetchone()

        saved_variant = connection.execute(
            """
            SELECT pv.variant_id
            FROM product_variants pv
            INNER JOIN products p
                ON pv.product_id = p.product_id
            WHERE p.product_name = ?
            """,
            (rollback_product.product_name,)
        ).fetchone()

        assert saved_product is None
        assert saved_variant is None

    print("Product creation rollback: PASSED")

    print("\nAll product service tests passed!")


if __name__ == "__main__":
    run_tests()
