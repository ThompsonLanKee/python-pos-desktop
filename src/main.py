
import sys

from PySide6.QtWidgets import QApplication

# Core
from src.core.database import Database
from src.core.session import SessionManager

# Repositories
from src.repositories import (
    UserRepository,
    PermissionRepository,
    RoleRepository
)

# Services
from src.services.auth_service import AuthService
from src.services.authorization_service import AuthorizationService
from src.services.sale_service import SaleService
from src.services.user_management_service import UserManagementService
from src.services.role_management_service import RoleManagementService
from src.services.product_service import ProductService

# Views
from src.views.login_view import LoginView
from src.views.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    # ==========================================
    # DATABASE
    # ==========================================

    database = Database()
    database.initialize()

    # ==========================================
    # SESSION
    # ==========================================

    session_manager = SessionManager()

    # ==========================================
    # REPOSITORIES
    # ==========================================

    user_repository = UserRepository(database)
    permission_repository = PermissionRepository(database)
    role_repository = RoleRepository(database)

    # ==========================================
    # SERVICES
    # ==========================================

    auth_service = AuthService(
        user_repository,
        session_manager
    )

    authorization_service = AuthorizationService(
        permission_repository
    )

    sale_service = SaleService(database)

    product_service = ProductService(database)

    user_management_service = UserManagementService(
        user_repository,
        role_repository,
        database
    )

    role_management_service = RoleManagementService(
        role_repository,
        permission_repository,
        database
    )

    # ==========================================
    # LOGIN WINDOW
    # ==========================================

    login_view = LoginView(auth_service)

    main_window = None

    def open_main_window(session):

        nonlocal main_window

        main_window = MainWindow(
            session,
            session_manager,
            authorization_service,
            sale_service,
            user_management_service,
            role_management_service,
            product_service
        )

        main_window.logout_requested.connect(show_login)

        login_view.hide()
        main_window.show()

    # ==========================================
    # LOGOUT
    # ==========================================

    def show_login():

        login_view.show()
        login_view.raise_()
        login_view.activateWindow()

    # ==========================================
    # START APPLICATION
    # ==========================================

    login_view.login_successful.connect(open_main_window)

    login_view.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
