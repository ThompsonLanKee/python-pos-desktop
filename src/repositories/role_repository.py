
from typing import Optional

from src.models import Role
from src.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository):

    def create(self, role: Role, connection=None) -> int:

        query = """
            INSERT INTO roles (role_name, description)
            VALUES (?, ?)
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query,
                (role.role_name, role.description)
            )
            return cursor.lastrowid

    def update(self, role: Role, connection=None) -> bool:

        if role.role_id is None:
            raise ValueError("Role ID is required.")

        query = """
            UPDATE roles
            SET role_name = ?,
                description = ?
            WHERE role_id = ?
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query,
                (
                    role.role_name,
                    role.description,
                    role.role_id
                )
            )
            return cursor.rowcount > 0

    def get_by_id(self, role_id: int) -> Optional[Role]:

        query = """
            SELECT *
            FROM roles
            WHERE role_id = ?
        """

        with self.connection() as connection:
            row = connection.execute(
                query, (role_id,)
            ).fetchone()

            return Role(**dict(row)) if row else None

    def get_by_name(self, role_name: str) -> Optional[Role]:

        query = """
            SELECT *
            FROM roles
            WHERE role_name = ? COLLATE NOCASE
        """

        with self.connection() as connection:
            row = connection.execute(
                query, (role_name.strip(),)
            ).fetchone()

            return Role(**dict(row)) if row else None

    def get_all(self) -> list[Role]:

        query = """
            SELECT *
            FROM roles
            ORDER BY role_name
        """

        with self.connection() as connection:
            rows = connection.execute(query).fetchall()

            return [
                Role(**dict(row))
                for row in rows
            ]

    def get_user_count(self, role_id: int) -> int:

        query = """
            SELECT COUNT(*)
            FROM user_roles
            WHERE role_id = ?
        """

        with self.connection() as connection:
            return connection.execute(
                query, (role_id,)
            ).fetchone()[0]

    def assign_to_user(
        self,
        user_id: int,
        role_id: int,
        connection=None
    ) -> None:

        query = """
            INSERT OR IGNORE INTO user_roles (user_id, role_id)
            VALUES (?, ?)
        """

        with self.connection_scope(connection) as conn:
            conn.execute(query, (user_id, role_id))

    def remove_from_user(
        self,
        user_id: int,
        role_id: int,
        connection=None
    ) -> bool:

        query = """
            DELETE FROM user_roles
            WHERE user_id = ? AND role_id = ?
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query, (user_id, role_id)
            )
            return cursor.rowcount > 0

    def set_user_roles(
        self,
        user_id: int,
        role_ids: list[int],
        connection=None
    ) -> None:

        with self.connection_scope(connection) as conn:

            conn.execute(
                "DELETE FROM user_roles WHERE user_id = ?",
                (user_id,)
            )

            for role_id in set(role_ids):
                conn.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (?, ?)
                    """,
                    (user_id, role_id)
                )

    def get_user_roles(self, user_id: int) -> list[Role]:

        query = """
            SELECT r.*
            FROM roles r
            INNER JOIN user_roles ur
                ON r.role_id = ur.role_id
            WHERE ur.user_id = ?
            ORDER BY r.role_name
        """

        with self.connection() as connection:
            rows = connection.execute(
                query, (user_id,)
            ).fetchall()

            return [
                Role(**dict(row))
                for row in rows
            ]
