
from src.models import (
    Category,
    Product,
    Color,
    Size,
    ProductVariant
)


def test_product_models():

    category = Category(
        category_name="Men's Clothing",
        description="Men's clothing products"
    )

    product = Product(
        product_name="Cotton T-Shirt",
        category_id=1,
        brand="Lankee"
    )

    color = Color(
        color_name="Black",
        hex_code="#000000"
    )

    size = Size(
        size_name="M",
        sort_order=2
    )

    variant = ProductVariant(
        product_id=1,
        color_id=1,
        size_id=1,
        sku="TS-BLK-M",
        cost_price=8000,
        selling_price=12000
    )

    assert category.category_name == "Men's Clothing"
    assert product.category_id == 1
    assert color.color_name == "Black"
    assert size.size_name == "M"
    assert variant.sku == "TS-BLK-M"

    print("Category model: PASSED")
    print("Product model: PASSED")
    print("Color model: PASSED")
    print("Size model: PASSED")
    print("ProductVariant model: PASSED")

    print("\nAll product model tests passed!")


if __name__ == "__main__":
    test_product_models()
