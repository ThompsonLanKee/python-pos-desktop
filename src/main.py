
import sys

from PySide6.QtWidgets import QApplication

from src.core.database import Database
from src.core.session import SessionManager

from src.repositories import (
    UserRepository,
    PermissionRepository
)

from src.services.auth_service import AuthService
from src.services.authorization_service import AuthorizationService

from src.views.login_view import LoginView
from src.views.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    # Database
    database = Database()
    database.initialize()

    # Session
    session_manager = SessionManager()

    # Repositories
    user_repository = UserRepository(database)
    permission_repository = PermissionRepository(database)

    # Services
    auth_service = AuthService(
        user_repository,
        session_manager
    )

    authorization_service = AuthorizationService(
        permission_repository
    )

    # Login window
    login_view = LoginView(auth_service)

    main_window = None

    def open_main_window(session):

        nonlocal main_window

        main_window = MainWindow(
            session,
            session_manager,
            authorization_service
        )

        main_window.logout_requested.connect(show_login)

        login_view.hide()
        main_window.show()

    def show_login():

        login_view.show()
        login_view.raise_()
        login_view.activateWindow()

    # Connect login signal
    login_view.login_successful.connect(open_main_window)

    login_view.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
