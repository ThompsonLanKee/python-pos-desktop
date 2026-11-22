
from src.core.database import Database

from src.models import User, Role, Permission

from src.repositories import (
    UserRepository,
    RoleRepository,
    PermissionRepository
)


def test_repositories():

    database = Database()
    database.initialize()

    user_repo = UserRepository(database)
    role_repo = RoleRepository(database)
    permission_repo = PermissionRepository(database)

    # 1. Create or retrieve a test user
    user = user_repo.get_by_username("test_admin")

    if user is None:
        user_id = user_repo.create(
            User(
                username="test_admin",
                password_hash="test_hash",
                full_name="Test Administrator"
            )
        )
        user = user_repo.get_by_id(user_id)

    assert user is not None
    assert user.username == "test_admin"
    assert user.is_active is True

    print("UserRepository: PASSED")

    # 2. Create or retrieve a role
    role = role_repo.get_by_name("Test Manager")

    if role is None:
        role_id = role_repo.create(
            Role(
                role_name="Test Manager",
                description="Test management role"
            )
        )
        role = role_repo.get_by_id(role_id)

    assert role is not None

    role_repo.assign_to_user(
        user.user_id,
        role.role_id
    )

    user_roles = role_repo.get_user_roles(user.user_id)

    assert any(r.role_id == role.role_id for r in user_roles)

    print("RoleRepository: PASSED")

    # 3. Create or retrieve permission
    permission = permission_repo.get_by_code(
        "TEST_REPORT_VIEW"
    )

    if permission is None:
        permission_id = permission_repo.create(
            Permission(
                permission_code="TEST_REPORT_VIEW",
                description="View test reports"
            )
        )
        permission = permission_repo.get_by_id(permission_id)

    assert permission is not None

    permission_repo.assign_to_role(
        role.role_id,
        permission.permission_id
    )

    permissions = permission_repo.get_user_permissions(
        user.user_id
    )

    assert any(
        p.permission_code == "TEST_REPORT_VIEW"
        for p in permissions
    )

    print("PermissionRepository: PASSED")


if __name__ == "__main__":
    test_repositories()
    print("\nAll repository tests passed!")
