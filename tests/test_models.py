from src.models import (
    User,
    Role,
    Permission,
    Category,
    Product,
    ProductVariant
)


def test_user():

    user = User(
        user_id=1,
        username="admin",
        password_hash="hashed_password",
        full_name="System Administrator"
    )

    assert user.username == "admin"
    assert user.is_active is True
    assert user.display_name == "System Administrator"

    user.deactivate()
    assert user.is_active is False

    user.activate()
    assert user.is_active is True

    print("User model: PASSED")


def test_role():

    role = Role(
        role_id=1,
        role_name="Administrator",
        description="Full system access"
    )

    assert role.role_name == "Administrator"

    role.rename("Manager")
    assert role.role_name == "Manager"

    print("Role model: PASSED")


def test_permission():

    permission = Permission(
        permission_id=1,
        permission_code="user_create",
        description="Create users"
    )

    assert permission.permission_code == "USER_CREATE"

    print("Permission model: PASSED")


def test_category():

    category = Category(
        category_id=1,
        category_name="  Beverages  "
    )

    assert category.category_name == "Beverages"

    category.deactivate()
    assert category.is_active is False

    print("Category model: PASSED")


def test_product_and_variant():

    product = Product(
        product_id=1,
        product_name="  T-Shirt  ",
        category_id=1
    )
    variant = ProductVariant(
        variant_id=1,
        product_id=1,
        sku="  TSHIRT-BLACK-M  ",
        cost_price=100,
        selling_price=150
    )

    assert product.product_name == "T-Shirt"
    assert variant.sku == "TSHIRT-BLACK-M"

    print("Product and variant models: PASSED")


if __name__ == "__main__":

    test_user()
    test_role()
    test_permission()
    test_category()
    test_product_and_variant()

    print("\nAll model tests passed!")
