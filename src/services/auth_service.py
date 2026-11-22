
from dataclasses import dataclass
from typing import Optional

from src.core.security import Security
from src.core.session import Session, SessionManager
from src.models import User
from src.repositories import UserRepository


@dataclass
class AuthResult:

    success: bool
    message: str
    user: Optional[User] = None
    session: Optional[Session] = None


class AuthService:

    """
    Handles user authentication and logout.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        session_manager: SessionManager
    ):

        self.user_repository = user_repository
        self.session_manager = session_manager

    def login(
        self,
        username: str,
        password: str
    ) -> AuthResult:

        # Validate input
        if not username or not username.strip():

            return AuthResult(
                success=False,
                message="Username is required."
            )

        if not password:

            return AuthResult(
                success=False,
                message="Password is required."
            )

        # Retrieve user
        user = self.user_repository.get_by_username(
            username.strip()
        )

        if user is None:

            return AuthResult(
                success=False,
                message="Invalid username or password."
            )

        # Verify password
        if not Security.verify_password(
            password,
            user.password_hash
        ):

            return AuthResult(
                success=False,
                message="Invalid username or password."
            )

        # Check account status
        if not user.is_active:

            return AuthResult(
                success=False,
                message="Your account is inactive."
            )

        # Create authenticated session
        session = self.session_manager.start(user)

        return AuthResult(
            success=True,
            message="Login successful.",
            user=user,
            session=session
        )

    def logout(self) -> None:

        self.session_manager.end()
