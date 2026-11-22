
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)

from PySide6.QtCore import Qt

from src.core.session import SessionManager


class MainWindow(QMainWindow):

    def __init__(self, session, session_manager: SessionManager):

        super().__init__()

        self.session = session
        self.session_manager = session_manager

        self.setWindowTitle("POS - Dashboard")
        self.resize(1000, 650)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        welcome = QLabel(
            f"Welcome, {session.full_name}!"
        )

        welcome.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        welcome.setStyleSheet(
            "font-size: 26px; font-weight: bold;"
        )

        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self.logout)

        layout.addWidget(welcome)
        layout.addWidget(logout_button)

        self.setCentralWidget(central_widget)

    def logout(self):

        self.session_manager.end()
        self.close()
