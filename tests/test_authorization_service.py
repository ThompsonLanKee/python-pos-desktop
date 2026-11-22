
from src.core.database import Database

from src.models import User, Role, Permission

from src.repositories import (
    UserRepository,
    RoleRepository,
    PermissionRepository
)

from src.services.authorization_service import (
    AuthorizationService
)


def test_authorization():

    database = Database()
    database.initialize()

    user_repo = UserRepository(database)
    role_repo = RoleRepository(database)
    permission_repo = PermissionRepository(database)

    authorization_service = AuthorizationService(
        permission_repo
    )

    # Create test user
    username = "rbac_test_user"

    user = user_repo.get_by_username(username)

    if user is None:

        user_id = user_repo.create(
            User(
                username=username,
                password_hash="test_hash",
                full_name="RBAC Test User"
            )
        )

        user = user_repo.get_by_id(user_id)

    # Create test role
    role_name = "RBAC Test Role"

    role = role_repo.get_by_name(role_name)

    if role is None:

        role_id = role_repo.create(
            Role(
                role_name=role_name,
                description="RBAC testing role"
            )
        )

        role = role_repo.get_by_id(role_id)

    # Create test permission
    permission_code = "TEST_PERMISSION"

    permission = permission_repo.get_by_code(
        permission_code
    )

    if permission is None:

        permission_id = permission_repo.create(
            Permission(
                permission_code=permission_code,
                description="Test permission"
            )
        )

        permission = permission_repo.get_by_id(
            permission_id
        )

    # Assign role to user
    user_roles = role_repo.get_user_roles(user.user_id)

    if not any(r.role_id == role.role_id for r in user_roles):

        role_repo.assign_to_user(
            user.user_id,
            role.role_id
        )

    # Assign permission to role
    role_permissions = (
        permission_repo.get_role_permissions(role.role_id)
    )

    if not any(
        p.permission_id == permission.permission_id
        for p in role_permissions
    ):

        permission_repo.assign_to_role(
            role.role_id,
            permission.permission_id
        )

    # Test permission retrieval
    permissions = authorization_service.get_user_permissions(
        user.user_id
    )

    assert "TEST_PERMISSION" in permissions

    print("Permission retrieval: PASSED")

    # Test permission validation
    assert authorization_service.has_permission(
        user.user_id,
        "TEST_PERMISSION"
    )

    print("Permission validation: PASSED")

    # Test unauthorized permission
    assert not authorization_service.has_permission(
        user.user_id,
        "UNKNOWN_PERMISSION"
    )

    print("Unauthorized access check: PASSED")

    # Test permission enforcement
    authorization_service.require_permission(
        user.user_id,
        "TEST_PERMISSION"
    )

    try:

        authorization_service.require_permission(
            user.user_id,
            "UNKNOWN_PERMISSION"
        )

        raise AssertionError("Permission check should have failed")

    except PermissionError:
        pass

    print("Permission enforcement: PASSED")

    print("\nAll authorization tests passed!")


if __name__ == "__main__":
    test_authorization()
