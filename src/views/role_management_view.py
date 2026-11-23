
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
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QAbstractItemView,
    QSplitter,
    QFrame,
    QCheckBox,
)


class RoleDialog(QDialog):
    """Create or edit a role and its permissions."""

    def __init__(
        self,
        permissions,
        role=None,
        assigned_permissions=None,
        parent=None
    ):
        super().__init__(parent)

        self.role = role
        self.permissions = permissions
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F7F5;
                color: #26352C;
            }
            QDialog QListWidget {
                background-color: #FFFFFF;
                color: #26352C;
                border: 1px solid #DCE5DE;
                border-radius: 6px;
            }
            QDialog QListWidget::item {
                padding: 8px;
            }
            QDialog QListWidget::indicator {
                width: 22px;
                height: 22px;
            }
            QDialog QListWidget::indicator:unchecked {
                background-color: #FFFFFF;
                border: 2px solid #536B5C;
                border-radius: 4px;
            }
            QDialog QListWidget::indicator:checked {
                background-color: #315D40;
                border: 2px solid #315D40;
                border-radius: 4px;
            }
        """)

        self.assigned_ids = {
            permission.permission_id
            for permission in (assigned_permissions or [])
        }

        self.setWindowTitle(
            "Edit Role" if role else "Create Role"
        )
        self.resize(650, 600)

        self._build_ui()

    def _build_ui(self):

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter role name")

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(
            "Enter role description"
        )

        form.addRow("Role Name:", self.name_input)
        form.addRow("Description:", self.description_input)

        layout.addLayout(form)

        permission_header = QHBoxLayout()

        permission_label = QLabel("Permissions")
        permission_label.setObjectName("section_title")

        self.select_all_button = QPushButton("Select All")
        self.clear_all_button = QPushButton("Clear All")

        self.select_all_button.clicked.connect(
            lambda: self._set_all_permissions(True)
        )

        self.clear_all_button.clicked.connect(
            lambda: self._set_all_permissions(False)
        )

        permission_header.addWidget(permission_label)
        permission_header.addStretch()
        permission_header.addWidget(self.select_all_button)
        permission_header.addWidget(self.clear_all_button)

        layout.addLayout(permission_header)

        self.permission_list = QListWidget()
        self.permission_list.setMinimumHeight(300)

        for permission in self.permissions:

            item = QListWidgetItem(
                f"{permission.permission_code}  —  "
                f"{permission.description or 'No description'}"
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                permission.permission_id
            )

            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )

            item.setCheckState(
                Qt.CheckState.Checked
                if permission.permission_id in self.assigned_ids
                else Qt.CheckState.Unchecked
            )

            self.permission_list.addItem(item)

        layout.addWidget(self.permission_list)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_button = QPushButton("Cancel")
        save_button = QPushButton(
            "Create Role" if self.role is None else "Save Changes"
        )

        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self._validate)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        if self.role:

            self.name_input.setText(self.role.role_name)

            self.description_input.setText(
                self.role.description or ""
            )

    def _set_all_permissions(self, checked: bool):

        state = (
            Qt.CheckState.Checked
            if checked
            else Qt.CheckState.Unchecked
        )

        for index in range(self.permission_list.count()):
            self.permission_list.item(index).setCheckState(state)

    def get_selected_permission_ids(self) -> list[int]:

        selected = []

        for index in range(self.permission_list.count()):

            item = self.permission_list.item(index)

            if item.checkState() == Qt.CheckState.Checked:
                selected.append(
                    item.data(Qt.ItemDataRole.UserRole)
                )

        return selected

    def _validate(self):

        if not self.name_input.text().strip():

            QMessageBox.warning(
                self,
                "Validation",
                "Role name is required."
            )
            return

        self.accept()

    def get_form_data(self) -> dict:

        return {
            "role_name": self.name_input.text().strip(),
            "description": self.description_input.text().strip(),
            "permission_ids": self.get_selected_permission_ids()
        }


class RoleManagementView(QWidget):
    """Role management interface."""

    def __init__(
        self,
        role_management_service,
        parent=None
    ):
        super().__init__(parent)

        self.role_management_service = role_management_service
        self.roles = []
        self.permissions = []
        self.permission_checkboxes = {}
        self._loading = False
        self._original_state = None

        self.setObjectName("role_management_view")
        self.setStyleSheet("""
            #role_management_view {
                background-color: #F5F7F5;
            }
            #roles_panel, #permissions_panel {
                background-color: #FFFFFF;
                border: 1px solid #DCE5DE;
                border-radius: 9px;
            }
            QLabel#panel_title {
                color: #203D2E;
                font-size: 17px;
                font-weight: 600;
            }
            QLabel#muted_text, QLabel#status_label {
                color: #718077;
            }
            QCheckBox {
                color: #26352C;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #FFFFFF;
                border: 2px solid #536B5C;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #315D40;
                border: 2px solid #315D40;
                border-radius: 4px;
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
            QListWidget#role_list {
                background-color: #FFFFFF;
                color: #26352C;
                border: none;
                outline: none;
            }
            QListWidget#role_list::item {
                border: 1px solid #E1E8E3;
                border-radius: 7px;
                padding: 9px;
                margin: 3px 0;
            }
            QListWidget#role_list::item:selected {
                background-color: #E8F1EB;
                color: #203D2E;
                border: 1px solid #78A889;
            }
            QTableWidget#permission_table {
                background-color: #FFFFFF;
                alternate-background-color: #F7F9F7;
                color: #26352C;
                gridline-color: #E4EAE5;
                selection-background-color: #E8F1EB;
                selection-color: #203D2E;
                border: 1px solid #DCE5DE;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #EAF1EC;
                color: #203D2E;
                padding: 9px;
                border: none;
                border-bottom: 1px solid #DCE5DE;
                font-weight: 600;
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
            QPushButton:disabled {
                color: #8A968E;
                background-color: #EEF1EF;
                border-color: #E0E5E1;
            }
        """)

        self._build_ui()
        self.load_roles()

    def _build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)

        roles_panel = QFrame()
        roles_panel.setObjectName("roles_panel")
        roles_layout = QVBoxLayout(roles_panel)
        roles_layout.setContentsMargins(16, 16, 16, 16)
        roles_layout.setSpacing(10)

        roles_title = QLabel("Roles")
        roles_title.setObjectName("panel_title")
        roles_layout.addWidget(roles_title)

        self.role_search_input = QLineEdit()
        self.role_search_input.setPlaceholderText("Filter roles...")
        self.role_search_input.textChanged.connect(
            self._filter_roles
        )
        roles_layout.addWidget(self.role_search_input)

        self.role_list = QListWidget()
        self.role_list.setObjectName("role_list")
        self.role_list.setSpacing(3)
        self.role_list.setWordWrap(True)
        self.role_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.role_list.currentItemChanged.connect(
            self._on_role_changed
        )
        roles_layout.addWidget(self.role_list, 1)

        self.role_count_label = QLabel("0 roles")
        self.role_count_label.setObjectName("muted_text")
        roles_layout.addWidget(self.role_count_label)

        create_title = QLabel("Create role")
        create_title.setObjectName("panel_title")
        roles_layout.addWidget(create_title)

        create_row = QHBoxLayout()
        self.new_role_input = QLineEdit()
        self.new_role_input.setPlaceholderText("e.g. Warehouse Manager")
        self.new_role_input.returnPressed.connect(self.create_role)
        create_row.addWidget(self.new_role_input, 1)

        self.create_button = QPushButton("Create")
        self.create_button.setObjectName("primary_button")
        self.create_button.clicked.connect(self.create_role)
        create_row.addWidget(self.create_button)
        roles_layout.addLayout(create_row)

        permissions_panel = QFrame()
        permissions_panel.setObjectName("permissions_panel")
        permissions_layout = QVBoxLayout(permissions_panel)
        permissions_layout.setContentsMargins(18, 16, 18, 16)
        permissions_layout.setSpacing(10)

        heading_row = QHBoxLayout()
        heading_text = QVBoxLayout()
        heading_text.setSpacing(3)

        self.permissions_title = QLabel("Permissions Matrix")
        self.permissions_title.setObjectName("panel_title")
        heading_text.addWidget(self.permissions_title)

        self.role_summary_label = QLabel(
            "Select a role to view and edit its access."
        )
        self.role_summary_label.setObjectName("muted_text")
        heading_text.addWidget(self.role_summary_label)
        heading_row.addLayout(heading_text, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_roles)
        heading_row.addWidget(self.refresh_button)
        permissions_layout.addLayout(heading_row)

        metadata_row = QHBoxLayout()
        metadata_form = QFormLayout()
        metadata_form.setHorizontalSpacing(12)
        metadata_form.setVerticalSpacing(8)

        self.role_name_input = QLineEdit()
        self.role_name_input.setPlaceholderText("Role name")
        self.role_description_input = QLineEdit()
        self.role_description_input.setPlaceholderText(
            "Describe what this role is for"
        )
        metadata_form.addRow("Role name", self.role_name_input)
        metadata_form.addRow("Description", self.role_description_input)
        metadata_row.addLayout(metadata_form, 1)
        permissions_layout.addLayout(metadata_row)

        filter_row = QHBoxLayout()
        self.permission_search_input = QLineEdit()
        self.permission_search_input.setPlaceholderText(
            "Filter permissions..."
        )
        self.permission_search_input.textChanged.connect(
            self._filter_permissions
        )
        filter_row.addWidget(self.permission_search_input, 1)

        self.select_visible_button = QPushButton("Select visible")
        self.select_visible_button.clicked.connect(
            lambda: self._set_visible_permissions(True)
        )
        filter_row.addWidget(self.select_visible_button)

        self.clear_visible_button = QPushButton("Clear visible")
        self.clear_visible_button.clicked.connect(
            lambda: self._set_visible_permissions(False)
        )
        filter_row.addWidget(self.clear_visible_button)
        permissions_layout.addLayout(filter_row)

        self.permission_table = QTableWidget()
        self.permission_table.setObjectName("permission_table")
        self.permission_table.setColumnCount(3)
        self.permission_table.setHorizontalHeaderLabels([
            "Permission",
            "Description",
            "Enabled"
        ])
        self.permission_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.permission_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.permission_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.permission_table.setAlternatingRowColors(True)
        self.permission_table.verticalHeader().setVisible(False)
        self.permission_table.verticalHeader().setDefaultSectionSize(38)
        self.permission_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.permission_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.permission_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        permissions_layout.addWidget(self.permission_table, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel("Select a role to get started.")
        self.status_label.setObjectName("status_label")
        footer.addWidget(self.status_label, 1)

        self.save_button = QPushButton("Save Changes")
        self.save_button.setObjectName("primary_button")
        self.save_button.clicked.connect(self.save_role)
        footer.addWidget(self.save_button)
        permissions_layout.addLayout(footer)

        splitter.addWidget(roles_panel)
        splitter.addWidget(permissions_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 760])
        main_layout.addWidget(splitter)

        self.role_name_input.textChanged.connect(self._update_dirty_state)
        self.role_description_input.textChanged.connect(
            self._update_dirty_state
        )
        self._set_editor_enabled(False)

    def load_roles(self, selected_role_id=None):

        try:
            self.roles = self.role_management_service.get_roles()
            self.permissions = (
                self.role_management_service.get_permissions()
            )

            if selected_role_id is None:
                selected_role_id = self._current_role_id()

            self._loading = True
            self.role_list.clear()

            selected_row = -1
            for role in self.roles:
                user_count = self.role_management_service.get_user_count(
                    role.role_id
                )
                item = QListWidgetItem(
                    f"{role.role_name}\n"
                    f"{user_count} user(s)"
                )
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    role.role_id
                )
                self.role_list.addItem(item)

                if role.role_id == selected_role_id:
                    selected_row = self.role_list.count() - 1

            self.role_count_label.setText(
                f"{len(self.roles)} role(s)"
            )

            if selected_row < 0 and self.role_list.count():
                selected_row = 0

            self.role_list.setCurrentRow(selected_row)
            self._loading = False
            if selected_row >= 0:
                self._display_role(self._current_role_id())
            else:
                self._display_role(None)

        except Exception as exc:
            self._loading = False
            QMessageBox.critical(
                self,
                "Load Error",
                f"Could not load roles:\n{exc}"
            )

    def _get_role(self, role_id):
        return next(
            (
                role for role in self.roles
                if role.role_id == role_id
            ),
            None
        )

    def _current_role_id(self):
        item = self.role_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _on_role_changed(self, current_item, previous_item):
        if self._loading:
            return

        if self._has_unsaved_changes():
            previous_role_id = (
                previous_item.data(Qt.ItemDataRole.UserRole)
                if previous_item is not None
                else None
            )
            previous_row = (
                self.role_list.row(previous_item)
                if previous_item is not None
                else -1
            )
            choice = QMessageBox.warning(
                self,
                "Unsaved Changes",
                "Save your changes before switching roles?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if choice == QMessageBox.StandardButton.Save:
                if not self._save_current_role(previous_role_id):
                    self._restore_role_row(previous_row)
                    return
            elif choice == QMessageBox.StandardButton.Cancel:
                self._restore_role_row(previous_row)
                return

        try:
            if current_item is None:
                self._display_role(None)
            else:
                self._display_role(
                    current_item.data(Qt.ItemDataRole.UserRole)
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Role Load Error",
                f"Could not load role details:\n{exc}"
            )
            if previous_item is not None:
                self._restore_role_row(
                    self.role_list.row(previous_item)
                )

    def _restore_role_row(self, row):
        self._loading = True
        self.role_list.setCurrentRow(row)
        self._loading = False

    def create_role(self):
        role_name = self.new_role_input.text().strip()
        if not role_name:
            QMessageBox.warning(
                self,
                "Validation",
                "Role name is required."
            )
            self.new_role_input.setFocus()
            return

        if self._has_unsaved_changes():
            choice = QMessageBox.warning(
                self,
                "Unsaved Changes",
                "Save your changes before creating a role?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if choice == QMessageBox.StandardButton.Save:
                if not self._save_current_role():
                    return
            elif choice == QMessageBox.StandardButton.Cancel:
                return

        try:
            role_id = self.role_management_service.create_role(
                role_name=role_name,
                description="",
                permission_ids=[]
            )
            self.new_role_input.clear()
            self.load_roles(selected_role_id=role_id)
            self.role_name_input.setFocus()
            self.status_label.setText(
                "Role created. Configure its permissions and save."
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Create Role Error",
                str(exc)
            )

    def _display_role(self, role_id):
        self._loading = True
        role = self._get_role(role_id) if role_id is not None else None
        self.permission_table.setRowCount(0)
        self.permission_checkboxes = {}

        if role is None:
            self.role_name_input.clear()
            self.role_description_input.clear()
            self.permissions_title.setText("Permissions Matrix")
            self.role_summary_label.setText(
                "Select a role to view and edit its access."
            )
            self._original_state = None
            self.status_label.setText("Select a role to get started.")
            self._set_editor_enabled(False)
            self._loading = False
            return

        assigned_permissions = (
            self.role_management_service.get_role_permissions(role.role_id)
        )
        assigned_ids = {
            permission.permission_id
            for permission in assigned_permissions
        }

        self.role_name_input.setText(role.role_name)
        self.role_description_input.setText(role.description or "")
        self.permissions_title.setText("Permissions Matrix")
        self.role_summary_label.setText(
            f"Editing {role.role_name} · "
            f"{self.role_management_service.get_user_count(role.role_id)} "
            "user(s) assigned"
        )

        self.permission_table.setRowCount(len(self.permissions))
        for row, permission in enumerate(self.permissions):
            code_item = QTableWidgetItem(permission.permission_code)
            code_item.setData(
                Qt.ItemDataRole.UserRole,
                permission.permission_id
            )
            code_item.setFlags(
                code_item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            description_item = QTableWidgetItem(
                permission.description or ""
            )
            description_item.setFlags(
                description_item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            enabled_checkbox = QCheckBox()
            enabled_checkbox.setChecked(
                permission.permission_id in assigned_ids
            )
            enabled_checkbox.toggled.connect(
                self._update_dirty_state
            )
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.addWidget(enabled_checkbox)
            self.permission_checkboxes[
                permission.permission_id
            ] = enabled_checkbox

            self.permission_table.setItem(row, 0, code_item)
            self.permission_table.setItem(row, 1, description_item)
            self.permission_table.setCellWidget(
                row,
                2,
                checkbox_container
            )

        self._original_state = self._current_state()
        self.status_label.setText(
            f"{len(assigned_ids)} permission(s) enabled."
        )
        self._set_editor_enabled(True)
        self._filter_permissions(self.permission_search_input.text())
        self._loading = False
        self._update_dirty_state()

    def _current_state(self):
        return (
            self.role_name_input.text().strip(),
            self.role_description_input.text().strip(),
            frozenset(self._selected_permission_ids())
        )

    def _selected_permission_ids(self):
        selected_ids = []
        for row in range(self.permission_table.rowCount()):
            permission_id = self.permission_table.item(
                row, 0
            ).data(Qt.ItemDataRole.UserRole)
            checkbox = self.permission_checkboxes.get(permission_id)
            if checkbox is not None and checkbox.isChecked():
                selected_ids.append(permission_id)
        return selected_ids

    def _has_unsaved_changes(self):
        return (
            self._original_state is not None
            and self._current_state() != self._original_state
        )

    def _update_dirty_state(self):
        if self._loading:
            return
        dirty = self._has_unsaved_changes()
        self.save_button.setEnabled(dirty)
        self.status_label.setText(
            "Unsaved changes" if dirty else "All changes saved."
        )

    def _set_visible_permissions(self, enabled):
        self._loading = True
        for row in range(self.permission_table.rowCount()):
            if not self.permission_table.isRowHidden(row):
                permission_id = self.permission_table.item(
                    row, 0
                ).data(Qt.ItemDataRole.UserRole)
                checkbox = self.permission_checkboxes.get(permission_id)
                if checkbox is not None:
                    checkbox.setChecked(enabled)
        self._loading = False
        self._update_dirty_state()

    def _filter_permissions(self, text):
        query = text.strip().lower()
        for row in range(self.permission_table.rowCount()):
            code = self.permission_table.item(row, 0)
            description = self.permission_table.item(row, 1)
            matches = (
                query in code.text().lower()
                or query in description.text().lower()
            )
            self.permission_table.setRowHidden(row, not matches)

    def _filter_roles(self, text):
        query = text.strip().lower()
        for row in range(self.role_list.count()):
            item = self.role_list.item(row)
            item.setHidden(query not in item.text().lower())

    def _set_editor_enabled(self, enabled):
        self.role_name_input.setEnabled(enabled)
        self.role_description_input.setEnabled(enabled)
        self.permission_search_input.setEnabled(enabled)
        self.select_visible_button.setEnabled(enabled)
        self.clear_visible_button.setEnabled(enabled)
        self.permission_table.setEnabled(enabled)
        self.save_button.setEnabled(False)

    def _save_current_role(self, role_id=None):
        if role_id is None:
            role_id = self._current_role_id()
        if role_id is None:
            return False

        role_name = self.role_name_input.text().strip()
        if not role_name:
            QMessageBox.warning(
                self,
                "Validation",
                "Role name is required."
            )
            self.role_name_input.setFocus()
            return False

        try:
            self.role_management_service.update_role(
                role_id=role_id,
                role_name=role_name,
                description=self.role_description_input.text().strip(),
                permission_ids=self._selected_permission_ids()
            )
            role = self._get_role(role_id)
            if role is not None:
                role.rename(role_name)
                role.update_description(
                    self.role_description_input.text().strip()
                )
            for row in range(self.role_list.count()):
                item = self.role_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == role_id:
                    user_count = (
                        self.role_management_service.get_user_count(
                            role_id
                        )
                    )
                    item.setText(
                        f"{role_name}\n"
                        f"{user_count} user(s)"
                    )
                    break
            self._original_state = self._current_state()
            self.save_button.setEnabled(False)
            self.status_label.setText("Changes saved.")
            return True

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save role changes:\n{exc}"
            )
            return False

    def save_role(self):
        if self._save_current_role():
            self.load_roles(selected_role_id=self._current_role_id())

    def refresh_roles(self):
        if not self._has_unsaved_changes():
            self.load_roles()
            return

        choice = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "Save your changes before refreshing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        if choice == QMessageBox.StandardButton.Save:
            if self._save_current_role():
                self.load_roles(selected_role_id=self._current_role_id())
        elif choice == QMessageBox.StandardButton.Discard:
            self.load_roles()
