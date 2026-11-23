
from typing import Optional
from sqlite3 import Row

from src.models import User
from src.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    """Handles database operations for User entities."""

    def create(self, user: User, connection=None) -> int:

        query = """
            INSERT INTO users (
                username,
                password_hash,
                full_name,
                is_active
            )
            VALUES (?, ?, ?, ?)
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query,
                (
                    user.username,
                    user.password_hash,
                    user.full_name,
                    int(user.is_active)
                )
            )
            return cursor.lastrowid

    def get_by_id(self, user_id: int) -> Optional[User]:

        query = "SELECT * FROM users WHERE user_id = ?"

        with self.connection() as connection:
            row = connection.execute(query, (user_id,)).fetchone()
            return self._to_user(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:

        query = "SELECT * FROM users WHERE username = ? COLLATE NOCASE"

        with self.connection() as connection:
            row = connection.execute(
                query, (username.strip(),)
            ).fetchone()
            return self._to_user(row) if row else None

    def get_all(self, search: str = "") -> list[User]:

        query = """
            SELECT *
            FROM users
            WHERE username LIKE ?
               OR full_name LIKE ?
            ORDER BY user_id
        """

        search_term = f"%{search.strip()}%"

        with self.connection() as connection:
            rows = connection.execute(
                query, (search_term, search_term)
            ).fetchall()

            return [self._to_user(row) for row in rows]

    def update(self, user: User, connection=None) -> bool:

        if user.user_id is None:
            raise ValueError("User ID is required.")

        query = """
            UPDATE users
            SET username = ?,
                full_name = ?,
                is_active = ?
            WHERE user_id = ?
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query,
                (
                    user.username,
                    user.full_name,
                    int(user.is_active),
                    user.user_id
                )
            )
            return cursor.rowcount > 0

    def set_active(
        self,
        user_id: int,
        is_active: bool,
        connection=None
    ) -> bool:

        query = """
            UPDATE users
            SET is_active = ?
            WHERE user_id = ?
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query, (int(is_active), user_id)
            )
            return cursor.rowcount > 0

    def update_password(
        self,
        user_id: int,
        password_hash: str,
        connection=None
    ) -> bool:

        query = """
            UPDATE users
            SET password_hash = ?
            WHERE user_id = ?
        """

        with self.connection_scope(connection) as conn:
            cursor = conn.execute(
                query, (password_hash, user_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def _to_user(row: Row) -> User:

        data = dict(row)
        data["is_active"] = bool(data["is_active"])

        return User(**data)
