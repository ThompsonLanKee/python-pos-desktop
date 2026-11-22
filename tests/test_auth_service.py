
from src.core.database import Database
from src.core.security import Security
from src.core.session import SessionManager

from src.models import User

from src.repositories import UserRepository

from src.services.auth_service import AuthService


def test_authentication():

    # Initialize database
    database = Database()
    database.initialize()

    # Initialize dependencies
    user_repository = UserRepository(database)
    session_manager = SessionManager()

    auth_service = AuthService(
        user_repository,
        session_manager
    )

    # Prepare test account
    username = "auth_test_user"
    password = "TestPassword123!"

    user = user_repository.get_by_username(username)

    if user is None:

        password_hash = Security.hash_password(password)

        user_id = user_repository.create(
            User(
                username=username,
                password_hash=password_hash,
                full_name="Authentication Test User"
            )
        )

    else:

        # Ensure the test account has the expected credentials
        with database.connect() as connection:

            connection.execute(
                """
                UPDATE users
                SET password_hash = ?, is_active = 1
                WHERE user_id = ?
                """,
                (
                    Security.hash_password(password),
                    user.user_id
                )
            )

    # TEST 1: Successful login
    result = auth_service.login(
        username,
        password
    )

    assert result.success is True
    assert result.session is not None
    assert session_manager.is_authenticated is True

    print("Successful login: PASSED")

    # Logout
    auth_service.logout()

    assert session_manager.is_authenticated is False

    # TEST 2: Incorrect password
    result = auth_service.login(
        username,
        "WrongPassword123!"
    )

    assert result.success is False
    assert session_manager.is_authenticated is False

    print("Incorrect password: PASSED")

    # TEST 3: Non-existing username
    result = auth_service.login(
        "unknown_user",
        password
    )

    assert result.success is False

    print("Unknown username: PASSED")

    # TEST 4: Inactive account
    user = user_repository.get_by_username(username)

    user_repository.set_active(user.user_id, False)

    result = auth_service.login(
        username,
        password
    )

    assert result.success is False
    assert session_manager.is_authenticated is False

    print("Inactive account: PASSED")

    # Restore test account
    user_repository.set_active(user.user_id, True)

    print("\nAll authentication tests passed!")


if __name__ == "__main__":
    test_authentication()
