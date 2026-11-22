
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
        Retrieve all permission codes assigned to a user.
        """

        permissions = (
            self.permission_repository.get_user_permissions(user_id)
        )

        return {
            permission.permission_code
            for permission in permissions
        }

    def has_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> bool:
        """
        Check whether a user has a specific permission.
        """

        permissions = self.get_user_permissions(user_id)

        return permission_code.upper() in permissions

    def has_any_permission(
        self,
        user_id: int,
        permission_codes: list[str]
    ) -> bool:
        """
        Check whether a user has at least one permission.
        """

        permissions = self.get_user_permissions(user_id)

        return any(
            code.upper() in permissions
            for code in permission_codes
        )

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
