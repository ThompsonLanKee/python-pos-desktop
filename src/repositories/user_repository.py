
from typing import Optional

from sqlite3 import Row

from src.models import User
from src.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    Handles database operations for User entities.
    """

    def create(self, user: User) -> int:
        """
        Create a new user and return the generated user ID.
        """

        query = """
            INSERT INTO users (
                username,
                password_hash,
                full_name,
                is_active
            )
            VALUES (?, ?, ?, ?)
        """

        with self.connection() as connection:

            cursor = connection.execute(
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
        """
        Retrieve a user by their primary key.
        """

        query = """
            SELECT *
            FROM users
            WHERE user_id = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (user_id,)
            ).fetchone()

            if row is None:
                return None

            return self._to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by their username.
        """

        query = """
            SELECT *
            FROM users
            WHERE username = ?
        """

        with self.connection() as connection:

            row = connection.execute(
                query,
                (username.strip(),)
            ).fetchone()

            if row is None:
                return None

            return self._to_user(row)

    def update(self, user: User) -> bool:
        """
        Update user profile information.
        Does not modify the password hash.
        """

        if user.user_id is None:
            raise ValueError("User ID is required.")

        query = """
            UPDATE users
            SET username = ?,
                full_name = ?,
                is_active = ?
            WHERE user_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    user.username,
                    user.full_name,
                    int(user.is_active),
                    user.user_id
                )
            )

            return cursor.rowcount > 0

    def set_active(self, user_id: int, is_active: bool) -> bool:
        """
        Activate or deactivate a user account.
        """

        query = """
            UPDATE users
            SET is_active = ?
            WHERE user_id = ?
        """

        with self.connection() as connection:

            cursor = connection.execute(
                query,
                (
                    int(is_active),
                    user_id
                )
            )

            return cursor.rowcount > 0

    def _to_user(self, row: Row) -> User:
        """
        Convert a SQLite row into a User entity.
        """

        data = dict(row)

        data["is_active"] = bool(data["is_active"])

        return User(**data)
