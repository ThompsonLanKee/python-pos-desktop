
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QCheckBox,
    QScrollArea,
    QMessageBox,
    QAbstractItemView,
    QFrame,
)

from PySide6.QtGui import QColor, QBrush


USER_MANAGEMENT_STYLESHEET = """
QFrame#users_panel {
    background-color: #FFFFFF;
    border: 1px solid #DCE5DE;
    border-radius: 9px;
}

QLabel#panel_title {
    color: #203D2E;
    font-size: 16px;
    font-weight: 600;
}

QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #F5F8F6;
    color: #26352C;
    gridline-color: #DCE5DE;
    border: 1px solid #DCE5DE;
    border-radius: 6px;
    outline: none;
}

QTableWidget::item {
    padding: 7px;
    border-bottom: 1px solid #E6ECE7;
}

QTableWidget::item:selected,
QTableWidget::item:selected:active,
QTableWidget::item:selected:!active {
    background-color: #D6EBDD;
    color: #203D2E;
}

QHeaderView::section {
    background-color: #EAF1EC;
    color: #203D2E;
    padding: 9px;
    border: none;
    border-bottom: 1px solid #DCE5DE;
    font-weight: 600;
}

QLineEdit {
    background-color: #FFFFFF;
    color: #26352C;
    border: 1px solid #C9D5CC;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #3F7653;
    selection-color: #FFFFFF;
}

QPushButton {
    background-color: #EAF1EC;
    color: #203D2E;
    border: 1px solid #D0DDD4;
    border-radius: 6px;
    padding: 8px 12px;
}

QPushButton:hover {
    background-color: #DCE9DF;
}

QPushButton#primary_button {
    background-color: #315D40;
    color: #FFFFFF;
    border: none;
}

QPushButton#primary_button:hover {
    background-color: #3F7653;
}

QPushButton#danger_button {
    background-color: #FBEDEC;
    color: #9F3434;
    border: 1px solid #EBCBC8;
}

QPushButton#danger_button:hover {
    background-color: #F5DEDC;
}

QPushButton:disabled {
    color: #8A968E;
    background-color: #EEF1EF;
    border-color: #E0E5E1;
}

QDialog {
    background-color: #F5F7F5;
    color: #26352C;
}

QDialog QLabel {
    background-color: transparent;
    color: #26352C;
}

QDialog QLabel#section_title {
    color: #203D2E;
}

QDialog QScrollArea {
    background-color: #FFFFFF;
    border: 1px solid #DCE5DE;
    border-radius: 6px;
}

QDialog QWidget#role_options {
    background-color: #FFFFFF;
}

QDialog QCheckBox {
    color: #26352C;
    spacing: 12px;
    padding: 7px 8px;
    border-radius: 5px;
}

QDialog QCheckBox:checked {
    color: #218838;
    font-weight: 600;
}

QDialog QCheckBox:hover {
    background-color: #EAF1EC;
}

QDialog QCheckBox::indicator {
    width: 22px;
    height: 22px;
}

QDialog QCheckBox::indicator:unchecked {
    background-color: #FFFFFF;
    border: 2px solid #536B5C;
    border-radius: 4px;
}

QDialog QCheckBox::indicator:checked {
    background-color: #315D40;
    border: 2px solid #315D40;
    border-radius: 4px;
}
"""


class UserDialog(QDialog):
    """Dialog for creating or editing a user."""

    def __init__(
        self,
        roles,
        user=None,
        assigned_roles=None,
        parent=None
    ):
        super().__init__(parent)

        self.setStyleSheet(USER_MANAGEMENT_STYLESHEET)
        self.user = user
        self.roles = roles
        self.assigned_roles = {
            role.role_id for role in (assigned_roles or [])
        }

        self.setWindowTitle(
            "Edit User" if user else "Create User"
        )
        self.setMinimumWidth(480)
        self.resize(500, 480)

        self._build_ui()

    def _build_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Enter full name")

        form.addRow("Username:", self.username_input)
        form.addRow("Full name:", self.full_name_input)

        if self.user is None:

            self.password_input = QLineEdit()
            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )
            self.password_input.setPlaceholderText(
                "Enter initial password"
            )

            form.addRow("Password:", self.password_input)

        else:
            self.password_input = None

        layout.addLayout(form)

        roles_label = QLabel("Assign Roles")
        roles_label.setObjectName("section_title")
        layout.addWidget(roles_label)

        roles_hint = QLabel(
            "Choose at least one role to grant the appropriate access."
        )
        roles_hint.setObjectName("page_subtitle")
        layout.addWidget(roles_hint)

        self.role_checkboxes = []
        self.role_list = QScrollArea()
        self.role_list.setWidgetResizable(True)
        self.role_list.setMinimumHeight(190)
        self.role_list.setFrameShape(QFrame.Shape.NoFrame)

        role_options = QWidget()
        role_options.setObjectName("role_options")
        role_options_layout = QVBoxLayout(role_options)
        role_options_layout.setContentsMargins(10, 8, 10, 8)
        role_options_layout.setSpacing(3)

        for role in self.roles:

            checkbox = QCheckBox(role.role_name)
            checkbox.setProperty("role_id", role.role_id)
            checkbox.setChecked(
                role.role_id in self.assigned_roles
            )
            self.role_checkboxes.append(checkbox)
            role_options_layout.addWidget(checkbox)

        role_options_layout.addStretch()
        self.role_list.setWidget(role_options)

        layout.addWidget(self.role_list)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        save_button = QPushButton(
            "Create User" if self.user is None else "Save Changes"
        )
        save_button.setObjectName("primary_button")

        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self._validate_and_accept)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        if self.user:

            self.username_input.setText(self.user.username)
            self.full_name_input.setText(self.user.full_name)

    def _validate_and_accept(self):

        if not self.username_input.text().strip():
            QMessageBox.warning(
                self,
                "Validation",
                "Username is required."
            )
            return

        if not self.full_name_input.text().strip():
            QMessageBox.warning(
                self,
                "Validation",
                "Full name is required."
            )
            return

        if self.password_input is not None:
            if not self.password_input.text():
                QMessageBox.warning(
                    self,
                    "Validation",
                    "Password is required."
                )
                return

        if not self.get_selected_role_ids():
            QMessageBox.warning(
                self,
                "Validation",
                "Please assign at least one role."
            )
            return

        self.accept()

    def get_selected_role_ids(self) -> list[int]:

        return [
            checkbox.property("role_id")
            for checkbox in self.role_checkboxes
            if checkbox.isChecked()
        ]

    def get_form_data(self) -> dict:

        return {
            "username": self.username_input.text().strip(),
            "full_name": self.full_name_input.text().strip(),
            "password": (
                self.password_input.text()
                if self.password_input is not None
                else None
            ),
            "role_ids": self.get_selected_role_ids()
        }


class PasswordResetDialog(QDialog):
    """Dialog for resetting a user's password."""

    def __init__(self, username, parent=None):
        super().__init__(parent)

        self.setStyleSheet(USER_MANAGEMENT_STYLESHEET)
        self.setWindowTitle("Reset Password")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setPlaceholderText(
            "Enter new password"
        )

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.confirm_input.setPlaceholderText(
            "Confirm new password"
        )

        form.addRow("Username:", QLabel(username))
        form.addRow("New password:", self.password_input)
        form.addRow("Confirm password:", self.confirm_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_button = QPushButton("Cancel")
        reset_button = QPushButton("Reset Password")
        reset_button.setObjectName("primary_button")

        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self._validate)

        buttons.addWidget(cancel_button)
        buttons.addWidget(reset_button)

        layout.addLayout(buttons)

    def _validate(self):

        password = self.password_input.text()
        confirmation = self.confirm_input.text()

        if not password:
            QMessageBox.warning(
                self,
                "Validation",
                "Password cannot be empty."
            )
            return

        if password != confirmation:
            QMessageBox.warning(
                self,
                "Validation",
                "Passwords do not match."
            )
            return

        self.accept()

    def get_password(self):
        return self.password_input.text()


class UserManagementView(QWidget):
    """User management interface."""

    def __init__(
        self,
        user_management_service,
        current_user_id,
        parent=None
    ):
        super().__init__(parent)

        self.user_management_service = user_management_service
        self.current_user_id = current_user_id

        self.users = []

        self.setStyleSheet(USER_MANAGEMENT_STYLESHEET)
        self._build_ui()
        self.load_users()

    def _build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

        # ------------------------------------------
        # TOOLBAR
        # ------------------------------------------

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search username or full name..."
        )
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(
            self.load_users
        )

        toolbar.addWidget(self.search_input, 1)

        self.add_button = QPushButton("+ Create User")
        self.add_button.setObjectName("primary_button")
        self.add_button.clicked.connect(self.create_user)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_user)

        self.reset_button = QPushButton("Reset Password")
        self.reset_button.clicked.connect(
            self.reset_password
        )

        self.toggle_button = QPushButton("Deactivate")
        self.toggle_button.clicked.connect(
            self.toggle_user_status
        )

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(
            self.load_users
        )

        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.reset_button)
        toolbar.addWidget(self.toggle_button)
        toolbar.addWidget(self.refresh_button)

        main_layout.addLayout(toolbar)

        # ------------------------------------------
        # USER TABLE
        # ------------------------------------------

        self.user_table = QTableWidget()

        self.user_table.setColumnCount(6)
        self.user_table.setHorizontalHeaderLabels([
            "ID",
            "Username",
            "Full Name",
            "Roles",
            "Status",
            "Created At"
        ])

        self.user_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.user_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.user_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.user_table.setAlternatingRowColors(True)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.verticalHeader().setDefaultSectionSize(40)

        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.user_table.itemSelectionChanged.connect(
            self._update_action_buttons
        )

        self.user_table.doubleClicked.connect(
            self.edit_user
        )

        users_panel = QFrame()
        users_panel.setObjectName("users_panel")
        panel_layout = QVBoxLayout(users_panel)
        panel_layout.setContentsMargins(14, 14, 14, 12)
        panel_layout.setSpacing(10)

        panel_header = QHBoxLayout()
        panel_title = QLabel("User Directory")
        panel_title.setObjectName("panel_title")
        panel_header.addWidget(panel_title)

        self.footer_label = QLabel("0 users")
        self.footer_label.setObjectName("page_subtitle")
        panel_header.addStretch()
        panel_header.addWidget(self.footer_label)
        panel_layout.addLayout(panel_header)

        panel_layout.addWidget(self.user_table)

        main_layout.addWidget(users_panel, 1)

        self._update_action_buttons()

    def load_users(self):

        try:
            search = self.search_input.text()

            self.users = self.user_management_service.get_users(
                search
            )

            self.user_table.setRowCount(0)

            for user in self.users:

                row = self.user_table.rowCount()
                self.user_table.insertRow(row)

                roles = self.user_management_service.get_user_roles(
                    user.user_id
                )

                role_names = ", ".join(
                    role.role_name for role in roles
                )

                values = [
                    str(user.user_id),
                    user.username,
                    user.full_name,
                    role_names,
                    "Active" if user.is_active else "Inactive",
                    user.created_at or ""
                ]

                for column, value in enumerate(values):

                    item = QTableWidgetItem(value)

                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        user.user_id
                    )

                    if column == 4:
                        item.setForeground(
                            QBrush(
                                QColor("#218838")
                                if user.is_active
                                else QColor("#DC3545")
                            )
                        )

                    self.user_table.setItem(
                        row,
                        column,
                        item
                    )

            self.footer_label.setText(
                f"{len(self.users)} user(s) found"
            )

            self._update_action_buttons()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Could not load users:\n{exc}"
            )

    def _get_selected_user(self):

        selected_rows = self.user_table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        user_id = self.user_table.item(
            selected_rows[0].row(),
            0
        ).data(Qt.ItemDataRole.UserRole)

        for user in self.users:
            if user.user_id == user_id:
                return user

        return None

    def _update_action_buttons(self):

        user = self._get_selected_user()
        has_selection = user is not None

        self.edit_button.setEnabled(has_selection)
        self.reset_button.setEnabled(has_selection)
        self.toggle_button.setEnabled(has_selection)

        if user:
            self.toggle_button.setText(
                "Deactivate" if user.is_active else "Activate"
            )
        else:
            self.toggle_button.setText("Deactivate")

    def create_user(self):

        try:
            roles = self.user_management_service.get_roles()

            if not roles:
                QMessageBox.warning(
                    self,
                    "No Roles",
                    "Create at least one role before creating a user."
                )
                return

            dialog = UserDialog(
                roles=roles,
                parent=self
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            data = dialog.get_form_data()

            self.user_management_service.create_user(
                username=data["username"],
                full_name=data["full_name"],
                password=data["password"],
                role_ids=data["role_ids"]
            )

            QMessageBox.information(
                self,
                "Success",
                "User created successfully."
            )

            self.load_users()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Create User Error",
                str(exc)
            )

    def edit_user(self):

        user = self._get_selected_user()

        if user is None:
            return

        try:
            roles = self.user_management_service.get_roles()

            assigned_roles = (
                self.user_management_service.get_user_roles(
                    user.user_id
                )
            )

            dialog = UserDialog(
                roles=roles,
                user=user,
                assigned_roles=assigned_roles,
                parent=self
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            data = dialog.get_form_data()

            self.user_management_service.update_user(
                user_id=user.user_id,
                username=data["username"],
                full_name=data["full_name"],
                role_ids=data["role_ids"]
            )

            QMessageBox.information(
                self,
                "Success",
                "User updated successfully."
            )

            self.load_users()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Update User Error",
                str(exc)
            )

    def reset_password(self):

        user = self._get_selected_user()

        if user is None:
            return

        dialog = PasswordResetDialog(
            username=user.username,
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.user_management_service.reset_password(
                user.user_id,
                dialog.get_password()
            )

            QMessageBox.information(
                self,
                "Success",
                "Password reset successfully."
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Password Reset Error",
                str(exc)
            )

    def toggle_user_status(self):

        user = self._get_selected_user()

        if user is None:
            return

        new_status = not user.is_active

        action = "activate" if new_status else "deactivate"

        confirmation = QMessageBox.question(
            self,
            "Confirm Account Status",
            f"Are you sure you want to {action} "
            f"'{user.username}'?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            self.user_management_service.set_user_active(
                user_id=user.user_id,
                is_active=new_status,
                current_user_id=self.current_user_id
            )

            QMessageBox.information(
                self,
                "Success",
                f"User {action}d successfully."
            )

            self.load_users()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Account Status Error",
                str(exc)
            )
