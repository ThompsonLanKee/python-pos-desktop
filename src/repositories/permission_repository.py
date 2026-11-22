
from typing import Optional

from src.models import Permission
from src.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository):

    def create(self, permission: Permission) -> int:

        query = """
            INSERT INTO permissions (
                permission_code,
                description
            )
            VALUES (?, ?)
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    permission.permission_code,
                    permission.description
                )
            )

            return cursor.lastrowid

    def get_by_id(
        self, permission_id: int
    ) -> Optional[Permission]:

        query = """
            SELECT *
            FROM permissions
            WHERE permission_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (permission_id,)
            ).fetchone()

            return Permission(**dict(row)) if row else None

    def get_by_code(
        self, permission_code: str
    ) -> Optional[Permission]:

        query = """
            SELECT *
            FROM permissions
            WHERE permission_code = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query, (permission_code.strip().upper(),)
            ).fetchone()

            return Permission(**dict(row)) if row else None

    def get_all(self) -> list[Permission]:

        query = """
            SELECT *
            FROM permissions
            ORDER BY permission_code
        """

        with self.connection() as connection:

            rows = connection.execute(query).fetchall()

            return [
                Permission(**dict(row))
                for row in rows
            ]

    def assign_to_role(
        self, role_id: int, permission_id: int
    ) -> None:

        query = """
            INSERT INTO role_permissions (
                role_id,
                permission_id
            )
            VALUES (?, ?)
        """

        with self.connection() as connection:
            connection.execute(
                query, (role_id, permission_id)
            )

    def remove_from_role(
        self, role_id: int, permission_id: int
    ) -> bool:

        query = """
            DELETE FROM role_permissions
            WHERE role_id = ? AND permission_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query, (role_id, permission_id)
            )

            return cursor.rowcount > 0

    def get_role_permissions(
        self, role_id: int
    ) -> list[Permission]:

        query = """
            SELECT p.*
            FROM permissions p
            INNER JOIN role_permissions rp
                ON p.permission_id = rp.permission_id
            WHERE rp.role_id = ?
            ORDER BY p.permission_code
        """

        with self.connection() as connection:

            rows = connection.execute(
                query, (role_id,)
            ).fetchall()

            return [
                Permission(**dict(row))
                for row in rows
            ]

    def get_user_permissions(
        self, user_id: int
    ) -> list[Permission]:

        query = """
            SELECT DISTINCT p.*
            FROM permissions p
            INNER JOIN role_permissions rp
                ON p.permission_id = rp.permission_id
            INNER JOIN user_roles ur
                ON rp.role_id = ur.role_id
            WHERE ur.user_id = ?
            ORDER BY p.permission_code
        """

        with self.connection() as connection:

            rows = connection.execute(
                query, (user_id,)
            ).fetchall()

            return [
                Permission(**dict(row))
                for row in rows
            ]
