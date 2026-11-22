
from typing import Optional

from src.models import Permission
from src.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository):
    """
    Handles database operations for permissions
    and role-permission relationships.
    """

    # ==========================================
    # CREATE
    # ==========================================

    def create(self, permission: Permission) -> int:
        """Create a new permission."""

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
                    permission.permission_code.strip().upper(),
                    permission.description
                )
            )

            return cursor.lastrowid

    # ==========================================
    # RETRIEVE
    # ==========================================

    def get_by_id(
        self,
        permission_id: int
    ) -> Optional[Permission]:
        """Retrieve a permission by ID."""

        query = """
            SELECT *
            FROM permissions
            WHERE permission_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (permission_id,)
            ).fetchone()

            return Permission(**dict(row)) if row else None

    def get_by_code(
        self,
        permission_code: str
    ) -> Optional[Permission]:
        """Retrieve a permission by its code."""

        query = """
            SELECT *
            FROM permissions
            WHERE permission_code = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (permission_code.strip().upper(),)
            ).fetchone()

            return Permission(**dict(row)) if row else None

    def get_all(self) -> list[Permission]:
        """Retrieve all permissions."""

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

    # ==========================================
    # ROLE-PERMISSION MANAGEMENT
    # ==========================================

    def assign_to_role(
        self,
        role_id: int,
        permission_id: int
    ) -> None:
        """Assign a permission to a role."""

        query = """
            INSERT OR IGNORE INTO role_permissions (
                role_id,
                permission_id
            )
            VALUES (?, ?)
        """

        with self.connection() as connection:

            connection.execute(
                query,
                (role_id, permission_id)
            )

    def remove_from_role(
        self,
        role_id: int,
        permission_id: int
    ) -> bool:
        """Remove a permission from a role."""

        query = """
            DELETE FROM role_permissions
            WHERE role_id = ?
              AND permission_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (role_id, permission_id)
            )

            return cursor.rowcount > 0

    def get_role_permissions(
        self,
        role_id: int
    ) -> list[Permission]:
        """Retrieve all permissions assigned to a role."""

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
                query,
                (role_id,)
            ).fetchall()

            return [
                Permission(**dict(row))
                for row in rows
            ]

    # ==========================================
    # USER PERMISSION RETRIEVAL
    # ==========================================

    def get_user_permissions(
        self,
        user_id: int
    ) -> list[Permission]:
        """
        Retrieve all permissions assigned to a user
        through their roles.
        """

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
                query,
                (user_id,)
            ).fetchall()

            return [
                Permission(**dict(row))
                for row in rows
            ]

    # ==========================================
    # DEBUGGING
    # ==========================================

    def debug_user_permissions(
        self,
        user_id: int
    ) -> None:
        """
        Display a user's roles and assigned permissions.
        Useful for RBAC troubleshooting.
        """

        query = """
            SELECT
                u.username,
                r.role_name,
                p.permission_code

            FROM users u

            INNER JOIN user_roles ur
                ON u.user_id = ur.user_id

            INNER JOIN roles r
                ON ur.role_id = r.role_id

            INNER JOIN role_permissions rp
                ON r.role_id = rp.role_id

            INNER JOIN permissions p
                ON rp.permission_id = p.permission_id

            WHERE u.user_id = ?

            ORDER BY
                r.role_name,
                p.permission_code
        """

        with self.connection() as connection:

            rows = connection.execute(
                query,
                (user_id,)
            ).fetchall()

            print("\n========== USER PERMISSION DEBUG ==========")
            print(f"User ID: {user_id}")

            for row in rows:
                print(
                    f"Username: {row['username']} | "
                    f"Role: {row['role_name']} | "
                    f"Permission: {row['permission_code']}"
                )

            print(f"Total permissions: {len(rows)}")
            print("===========================================\n")
