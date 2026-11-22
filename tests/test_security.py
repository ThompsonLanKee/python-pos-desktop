
from src.core.security import Security
from src.core.session import SessionManager
from src.models import User


def test_password_hashing():

    password = "MySecurePassword123!"

    # Generate password hashes
    hash_one = Security.hash_password(password)
    hash_two = Security.hash_password(password)

    # Different salts should produce different hashes
    assert hash_one != hash_two

    # Correct password
    assert Security.verify_password(
        password, hash_one
    ) is True

    # Incorrect password
    assert Security.verify_password(
        "WrongPassword123!", hash_one
    ) is False

    # Invalid hash
    assert Security.verify_password(
        password, "invalid_hash"
    ) is False

    print("Password hashing: PASSED")


def test_session_management():

    session_manager = SessionManager()

    user = User(
        user_id=1,
        username="admin",
        password_hash="test_hash",
        full_name="System Administrator"
    )

    # Initially no session
    assert session_manager.is_authenticated is False

    # Start session
    session = session_manager.start(user)

    assert session_manager.is_authenticated is True
    assert session_manager.current_user_id == 1
    assert session.username == "admin"

    print("Session creation: PASSED")

    # End session
    session_manager.end()

    assert session_manager.is_authenticated is False
    assert session_manager.current is None

    print("Session termination: PASSED")


if __name__ == "__main__":

    test_password_hashing()
    test_session_management()

    print("\nAll security tests passed!")
