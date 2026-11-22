
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QMessageBox,
    QFrame
)

from PySide6.QtCore import Qt, Signal

from src.services.auth_service import AuthService


class LoginView(QWidget):

    login_successful = Signal(object)

    def __init__(self, auth_service: AuthService):

        super().__init__()

        self.auth_service = auth_service

        self.setWindowTitle("POS - Login")
        self.setFixedSize(430, 540)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(40, 35, 40, 35)
        main_layout.setSpacing(15)

        # Application title
        title = QLabel("POS SYSTEM")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")

        subtitle = QLabel("Sign in to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")

        # Login card
        card = QFrame()
        card.setObjectName("loginCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        # Username
        username_label = QLabel("Username")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(42)

        # Password
        password_label = QLabel("Password")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setMinimumHeight(42)

        # Show password
        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(
            self.toggle_password_visibility
        )

        # Remember username
        self.remember_username = QCheckBox("Remember username")

        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setMinimumHeight(45)

        self.login_button.clicked.connect(self.handle_login)

        # Error message
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        # Add widgets
        card_layout.addWidget(username_label)
        card_layout.addWidget(self.username_input)

        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)

        card_layout.addWidget(self.show_password)
        card_layout.addWidget(self.remember_username)

        card_layout.addWidget(self.login_button)

        card_layout.addWidget(self.error_label)

        main_layout.addStretch()
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(20)
        main_layout.addWidget(card)
        main_layout.addStretch()

        footer = QLabel("Python POS Application")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(footer)

        self.password_input.returnPressed.connect(
            self.handle_login
        )

    def toggle_password_visibility(self, checked):

        if checked:

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal
            )

        else:

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )

    def handle_login(self):

        username = self.username_input.text()
        password = self.password_input.text()

        self.error_label.clear()

        self.login_button.setEnabled(False)

        try:

            result = self.auth_service.login(
                username,
                password
            )

            if result.success:

                self.password_input.clear()

                self.login_successful.emit(result.session)

            else:

                self.error_label.setText(result.message)

        except Exception:

            self.error_label.setText(
                "An unexpected error occurred. Please try again."
            )

        finally:

            self.login_button.setEnabled(True)

    def apply_styles(self):

        self.setStyleSheet("""
            QWidget {
                background-color: #F3F6F4;
                color: #26372D;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QLabel#title {
                font-size: 27px;
                font-weight: bold;
                color: #203D2E;
            }

            QLabel#subtitle {
                color: #718078;
                font-size: 14px;
            }

            QFrame#loginCard {
                background-color: white;
                border: 1px solid #DCE5DE;
                border-radius: 12px;
            }

            QLineEdit {
                background-color: #F8FAF8;
                border: 1px solid #D5DED7;
                border-radius: 6px;
                padding: 8px;
            }

            QLineEdit:focus {
                border: 2px solid #397A52;
            }

            QPushButton {
                background-color: #203D2E;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #315B43;
            }

            QPushButton:disabled {
                background-color: #84978A;
            }

            QCheckBox {
                spacing: 7px;
            }

            QLabel#errorLabel {
                color: #C0392B;
            }
        """)
