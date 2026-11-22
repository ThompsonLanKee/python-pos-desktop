
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.models import User


@dataclass(frozen=True)
class Session:

    user_id: int
    username: str
    full_name: str
    login_at: datetime


class SessionManager:

    """
    Manages the currently authenticated user session.
    """

    def __init__(self):

        self._current_session: Optional[Session] = None

    def start(self, user: User) -> Session:

        if user.user_id is None:
            raise ValueError("User ID is required.")

        if not user.is_active:
            raise ValueError("Inactive users cannot start a session.")

        session = Session(
            user_id=user.user_id,
            username=user.username,
            full_name=user.full_name,
            login_at=datetime.now(timezone.utc)
        )

        self._current_session = session

        return session

    def end(self) -> None:

        self._current_session = None

    @property
    def current(self) -> Optional[Session]:

        return self._current_session

    @property
    def is_authenticated(self) -> bool:

        return self._current_session is not None

    @property
    def current_user_id(self) -> Optional[int]:

        if self._current_session is None:
            return None

        return self._current_session.user_id
