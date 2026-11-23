
import sqlite3

from src.core.security import Security
from src.models import User
from src.repositories import UserRepository, RoleRepository


class UserManagementService:

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        database
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.database = database

    def get_users(self, search: str = "") -> list[User]:
        return self.user_repository.get_all(search)

    def get_roles(self):
        return self.role_repository.get_all()

    def get_user_roles(self, user_id: int):
        return self.role_repository.get_user_roles(user_id)

    def create_user(
        self,
        username: str,
        full_name: str,
        password: str,
        role_ids: list[int]
    ) -> int:

        username = username.strip()
        full_name = full_name.strip()

        if not username:
            raise ValueError("Username is required.")

        if not full_name:
            raise ValueError("Full name is required.")

        if not password:
            raise ValueError("Password is required.")

        if not role_ids:
            raise ValueError("Assign at least one role.")

        if self.user_repository.get_by_username(username):
            raise ValueError("Username already exists.")

        password_hash = Security.hash_password(password)

        user = User(
            username=username,
            full_name=full_name,
            password_hash=password_hash,
            is_active=True
        )

        try:
            with self.database.transaction() as connection:

                user_id = self.user_repository.create(
                    user, connection=connection
                )

                self.role_repository.set_user_roles(
                    user_id,
                    role_ids,
                    connection=connection
                )

                return user_id

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Could not create user. Check the username and selected roles."
            ) from exc

    def update_user(
        self,
        user_id: int,
        username: str,
        full_name: str,
        role_ids: list[int]
    ) -> None:

        username = username.strip()
        full_name = full_name.strip()

        if not username:
            raise ValueError("Username is required.")

        if not full_name:
            raise ValueError("Full name is required.")

        if not role_ids:
            raise ValueError("Assign at least one role.")

        existing = self.user_repository.get_by_username(username)

        if existing and existing.user_id != user_id:
            raise ValueError("Username already exists.")

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        user.username = username
        user.full_name = full_name

        try:
            with self.database.transaction() as connection:

                if not self.user_repository.update(
                    user, connection=connection
                ):
                    raise ValueError("User could not be updated.")

                self.role_repository.set_user_roles(
                    user_id,
                    role_ids,
                    connection=connection
                )

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Could not update user. Check the username and selected roles."
            ) from exc

    def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> None:

        if not new_password:
            raise ValueError("Password cannot be empty.")

        if self.user_repository.get_by_id(user_id) is None:
            raise ValueError("User not found.")

        password_hash = Security.hash_password(new_password)

        if not self.user_repository.update_password(
            user_id, password_hash
        ):
            raise ValueError("Password could not be updated.")

    def set_user_active(
        self,
        user_id: int,
        is_active: bool,
        current_user_id: int
    ) -> None:

        if user_id == current_user_id and not is_active:
            raise ValueError(
                "You cannot deactivate your own signed-in account."
            )

        if self.user_repository.get_by_id(user_id) is None:
            raise ValueError("User not found.")

        if not self.user_repository.set_active(user_id, is_active):
            raise ValueError("Account status could not be updated.")
