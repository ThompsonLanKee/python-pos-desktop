
from src.repositories import PermissionRepository


class AuthorizationService:
    """
    Handles role-based access control (RBAC).
    """

    def __init__(
        self,
        permission_repository: PermissionRepository
    ):
        self.permission_repository = permission_repository

    def get_user_permissions(self, user_id: int) -> set[str]:
        """
        Retrieve all normalized permission codes assigned to a user.
        """

        permissions = (
            self.permission_repository.get_user_permissions(user_id)
        )

        return {
            permission.permission_code.strip().upper()
            for permission in permissions
            if permission.permission_code
        }

    def has_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> bool:
        """
        Check whether a user has a specific permission.
        """

        if not permission_code:
            return False

        permissions = self.get_user_permissions(user_id)

        return permission_code.strip().upper() in permissions

    def has_any_permission(
        self,
        user_id: int,
        permission_codes: list[str]
    ) -> bool:
        """
        Check whether a user has at least one permission.
        """

        permissions = self.get_user_permissions(user_id)

        required_permissions = {
            code.strip().upper()
            for code in permission_codes
            if code
        }

        return bool(permissions.intersection(required_permissions))

    def require_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> None:
        """
        Raise an exception when permission is missing.
        """

        if not self.has_permission(user_id, permission_code):
            raise PermissionError(
                f"Access denied: {permission_code}"
            )
