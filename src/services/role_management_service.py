
import sqlite3

from src.models import Role
from src.repositories import RoleRepository, PermissionRepository


class RoleManagementService:

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        database
    ):
        self.role_repository = role_repository
        self.permission_repository = permission_repository
        self.database = database

    def get_roles(self) -> list[Role]:
        return self.role_repository.get_all()

    def get_permissions(self):
        return self.permission_repository.get_all()

    def get_role_permissions(self, role_id: int):
        return self.permission_repository.get_role_permissions(
            role_id
        )

    def get_user_count(self, role_id: int) -> int:
        return self.role_repository.get_user_count(role_id)

    def create_role(
        self,
        role_name: str,
        description: str,
        permission_ids: list[int]
    ) -> int:

        role_name = role_name.strip()
        description = description.strip()

        if not role_name:
            raise ValueError("Role name is required.")

        existing = self.role_repository.get_by_name(role_name)

        if existing:
            raise ValueError("Role name already exists.")

        role = Role(
            role_name=role_name,
            description=description or None
        )

        try:
            with self.database.transaction() as connection:

                role_id = self.role_repository.create(
                    role,
                    connection=connection
                )

                self.permission_repository.set_role_permissions(
                    role_id,
                    permission_ids,
                    connection=connection
                )

                return role_id

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Could not create role. The role name or permissions may be invalid."
            ) from exc

    def update_role(
        self,
        role_id: int,
        role_name: str,
        description: str,
        permission_ids: list[int]
    ) -> None:

        role_name = role_name.strip()
        description = description.strip()

        if not role_name:
            raise ValueError("Role name is required.")

        existing = self.role_repository.get_by_name(role_name)

        if existing and existing.role_id != role_id:
            raise ValueError("Role name already exists.")

        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise ValueError("Role not found.")

        role.rename(role_name)
        role.update_description(description)

        try:
            with self.database.transaction() as connection:

                if not self.role_repository.update(
                    role,
                    connection=connection
                ):
                    raise ValueError("Role could not be updated.")

                self.permission_repository.set_role_permissions(
                    role_id,
                    permission_ids,
                    connection=connection
                )

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Could not update role. Check the role name and permissions."
            ) from exc
