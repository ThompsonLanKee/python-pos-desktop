
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.database import Database
from src.core.session import SessionManager

from src.repositories import UserRepository

from src.services.auth_service import AuthService

from src.views.login_view import LoginView
from src.views.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    app.setApplicationName("Python POS")

    # Initialize database
    database = Database()
    database.initialize()

    # Initialize repositories
    user_repository = UserRepository(database)

    # Initialize session manager
    session_manager = SessionManager()

    # Initialize authentication service
    auth_service = AuthService(
        user_repository,
        session_manager
    )

    # Initialize login window
    login_view = LoginView(auth_service)

    main_window = None

    def open_main_window(session):

        nonlocal main_window

        main_window = MainWindow(
            session,
            session_manager
        )

        main_window.show()
        login_view.hide()

    login_view.login_successful.connect(
        open_main_window
    )

    login_view.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
