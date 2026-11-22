
from uuid import uuid4

from src.core.database import Database
from src.models import Category, Product
from src.repositories import CategoryRepository
from src.services.product_service import ProductService


def run_tests():

    database = Database()
    database.initialize()

    category_repo = CategoryRepository(database)
    service = ProductService(database)

    suffix = uuid4().hex[:8]

    category_id = category_repo.create(
        Category(
            category_name=f"Retrieval Test {suffix}"
        )
    )

    product = Product(
        product_name=f"Test Product {suffix}",
        category_id=category_id,
        brand="Test Brand"
    )

    product_id = service.create_product(
        product,
        [
            {
                "sku": f"TEST-SKU-{suffix}",
                "color_id": None,
                "size_id": None,
                "cost_price": 1000,
                "selling_price": 1500
            }
        ]
    )

    # Test product details.
    details = service.get_product_details(product_id)

    assert details is not None
    assert details["product"]["product_id"] == product_id
    assert len(details["variants"]) == 1

    print("Product details retrieval: PASSED")

    # Test all products.
    products = service.get_all_products()

    assert any(
        item.product_id == product_id
        for item in products
    )

    print("All products retrieval: PASSED")

    # Test category filtering.
    category_products = service.get_products_by_category(
        category_id
    )

    assert any(
        item.product_id == product_id
        for item in category_products
    )

    print("Category product filtering: PASSED")

    # Test searching.
    results = service.search_products(
        f"Test Product {suffix}"
    )

    assert any(
        item.product_id == product_id
        for item in results
    )

    print("Product search: PASSED")

    # Test updating.
    product.product_id = product_id
    product.product_name = f"Updated Product {suffix}"

    assert service.update_product(product)

    updated = service.get_product_details(product_id)

    assert (
        updated["product"]["product_name"]
        == f"Updated Product {suffix}"
    )

    print("Product update: PASSED")

    # Test deactivation.
    assert service.set_product_active(
        product_id,
        False
    )

    assert not service.set_product_active(
        999999999,
        False
    )

    print("Product activation/deactivation: PASSED")

    print("\nAll ProductService retrieval tests passed!")


if __name__ == "__main__":
    run_tests()
