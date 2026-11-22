from src.models import User, Role, Permission


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


if __name__ == "__main__":

    test_user()
    test_role()
    test_permission()

    print("\nAll model tests passed!")
