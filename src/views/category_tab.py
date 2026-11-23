
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QAbstractItemView,
)

from src.services.category_service import CategoryService


class CategoryDialog(QDialog):
    """Dialog for creating and editing categories."""

    def __init__(
        self,
        categories,
        category=None,
        parent=None,
    ):
        super().__init__(parent)

        self.categories = categories
        self.category = category

        self.setWindowTitle(
            "Edit Category" if category else "Add Category"
        )
        self.setMinimumWidth(480)
        self.setAutoFillBackground(True)

        self.setStyleSheet("""
            QDialog, QDialog QWidget {
                background-color: #F5F8F6;
                color: #203D2E;
            }

            QDialog QLabel {
                color: #203D2E;
                background-color: transparent;
                font-size: 13px;
            }

            QDialog QLineEdit,
            QDialog QTextEdit,
            QDialog QComboBox {
                background-color: #FFFFFF;
                color: #203D2E;
                border: 1px solid #C8D8CD;
                border-radius: 7px;
                padding: 9px;
                selection-background-color: #B9DCC5;
                selection-color: #203D2E;
            }

            QDialog QLineEdit:focus,
            QDialog QTextEdit:focus,
            QDialog QComboBox:focus {
                border: 2px solid #43845A;
            }

            QDialog QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #203D2E;
                selection-background-color: #D6EBDD;
                selection-color: #203D2E;
            }

            QDialog QPushButton {
                background-color: #E6EEE8;
                color: #203D2E;
                border: 1px solid #C8D8CD;
                border-radius: 7px;
                padding: 9px 16px;
                min-width: 65px;
            }

            QDialog QPushButton:hover {
                background-color: #D6EBDD;
            }

            QDialog QPushButton#primary_button {
                background-color: #315D40;
                color: #FFFFFF;
                border: none;
                font-weight: 600;
            }

            QDialog QPushButton#primary_button:hover {
                background-color: #43845A;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setMaxLength(100)
        self.name_input.setPlaceholderText("Enter category name")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Optional category description"
        )
        self.description_input.setFixedHeight(90)

        self.parent_combo = QComboBox()
        self.parent_combo.addItem("No Parent", None)

        editing_id = (
            self.category["category_id"]
            if self.category else None
        )

        for item in self.categories:
            if not item["is_active"]:
                continue

            if item["category_id"] == editing_id:
                continue

            self.parent_combo.addItem(
                item["category_name"],
                item["category_id"]
            )

        form.addRow("Category Name *", self.name_input)
        form.addRow("Description", self.description_input)
        form.addRow("Parent Category", self.parent_combo)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save")
        save_button.setObjectName("primary_button")
        save_button.clicked.connect(self.accept)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        if self.category:
            self.name_input.setText(
                self.category["category_name"]
            )
            self.description_input.setPlainText(
                self.category["description"] or ""
            )

            parent_id = self.category["parent_category_id"]
            index = self.parent_combo.findData(parent_id)

            if index >= 0:
                self.parent_combo.setCurrentIndex(index)

    def get_form_data(self):
        return {
            "category_name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "parent_category_id": self.parent_combo.currentData(),
        }


class CategoryTab(QWidget):
    """Category management interface."""

    def __init__(self, database, parent=None):
        super().__init__(parent)

        self.category_service = CategoryService(database)
        self.categories = []

        self.setStyleSheet("""
            QWidget {
                background-color: #F5F8F6;
                color: #203D2E;
            }

            QLabel {
                color: #203D2E;
                background-color: transparent;
            }

            QLineEdit, QComboBox, QTextEdit, QTableWidget {
                background-color: #FFFFFF;
                color: #26352C;
                border: 1px solid #DCE5DE;
                border-radius: 7px;
            }

            QLineEdit, QComboBox {
                padding: 8px;
            }

            QTableWidget {
                alternate-background-color: #F5F8F6;
                gridline-color: #E5EAE6;
                selection-background-color: #C7E4D0;
                selection-color: #203D2E;
            }

            QTableWidget::item:selected {
                background-color: #C7E4D0;
                color: #203D2E;
            }

            QTableWidget::item:hover {
                background-color: #E4F0E7;
                color: #203D2E;
            }

            QHeaderView::section {
                background-color: #EAF1EC;
                color: #203D2E;
                padding: 10px;
                border: none;
                font-weight: 600;
            }

            QPushButton {
                background-color: #EAF1EC;
                color: #203D2E;
                border: 1px solid #D0DDD4;
                border-radius: 6px;
                padding: 8px 13px;
            }

            QPushButton:hover {
                background-color: #DCE9DF;
            }

            QPushButton#primary_button {
                background-color: #315D40;
                color: white;
                border: none;
            }

            QPushButton#primary_button:hover {
                background-color: #3F7653;
            }

            QPushButton:disabled {
                color: #8A968E;
                background-color: #EEF1EF;
            }
        """)

        self._build_ui()
        self.load_categories()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        heading = QLabel("Categories")
        heading.setObjectName("section_title")

        subtitle = QLabel(
            "Organize products into categories and subcategories."
        )
        subtitle.setStyleSheet("color: #718077;")

        layout.addWidget(heading)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search categories..."
        )
        self.search_input.textChanged.connect(
            self._filter_categories
        )

        toolbar.addWidget(self.search_input, 1)

        self.add_button = QPushButton("Add Category")
        self.add_button.setObjectName("primary_button")
        self.add_button.clicked.connect(self.add_category)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_category)

        self.status_button = QPushButton("Deactivate")
        self.status_button.clicked.connect(
            self.toggle_category_status
        )

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(
            self.load_categories
        )

        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.status_button)
        toolbar.addWidget(self.refresh_button)

        layout.addLayout(toolbar)

        self.category_table = QTableWidget(0, 5)
        self.category_table.setHorizontalHeaderLabels([
            "Category",
            "Parent Category",
            "Description",
            "Status",
            "ID",
        ])

        self.category_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.category_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.category_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.category_table.setAlternatingRowColors(True)
        self.category_table.verticalHeader().setVisible(False)

        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )

        self.category_table.setColumnHidden(4, True)

        self.category_table.itemSelectionChanged.connect(
            self._update_buttons
        )

        layout.addWidget(self.category_table, 1)

        self.result_label = QLabel("0 categories")
        self.result_label.setStyleSheet("color: #718077;")
        layout.addWidget(self.result_label)

        self._update_buttons()

    # ==========================================
    # MESSAGE BOXES
    # ==========================================

    def _style_message_box(self, box):
        box.setStyleSheet("""
            QMessageBox {
                background-color: #F5F8F6;
            }

            QMessageBox QLabel {
                color: #203D2E;
                background-color: transparent;
                min-width: 280px;
                font-size: 13px;
            }

            QMessageBox QPushButton {
                background-color: #315D40;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                min-width: 70px;
            }

            QMessageBox QPushButton:hover {
                background-color: #43845A;
            }
        """)

    def _show_message(self, title, message, icon=QMessageBox.Icon.Information):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setIcon(icon)
        self._style_message_box(box)
        box.exec()

    def _confirm_action(self, title, message):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Question)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)
        self._style_message_box(box)
        return box.exec() == QMessageBox.StandardButton.Yes

    # ==========================================
    # LOAD AND DISPLAY
    # ==========================================

    def load_categories(self):
        try:
            selected_id = self._selected_category_id()

            self.categories = (
                self.category_service.get_all_categories()
            )

            self._display_categories(
                self.search_input.text(),
                selected_id
            )

        except Exception as exc:
            self._show_message(
                "Category Load Error",
                f"Could not load categories:\n{exc}",
                QMessageBox.Icon.Critical
            )

    def _display_categories(
        self,
        keyword="",
        selected_id=None,
    ):
        keyword = keyword.strip().casefold()

        filtered = [
            category for category in self.categories
            if keyword in category["category_name"].casefold()
            or keyword in (category["description"] or "").casefold()
            or keyword in (
                category["parent_category_name"] or ""
            ).casefold()
        ]

        self.category_table.setRowCount(len(filtered))
        selected_row = -1

        for row, category in enumerate(filtered):
            name_item = QTableWidgetItem(
                category["category_name"]
            )
            name_item.setData(
                Qt.ItemDataRole.UserRole,
                category["category_id"]
            )

            parent_item = QTableWidgetItem(
                category["parent_category_name"] or "—"
            )

            description_item = QTableWidgetItem(
                category["description"] or ""
            )

            status_item = QTableWidgetItem(
                "Active" if category["is_active"] else "Inactive"
            )

            id_item = QTableWidgetItem(
                str(category["category_id"])
            )

            self.category_table.setItem(row, 0, name_item)
            self.category_table.setItem(row, 1, parent_item)
            self.category_table.setItem(row, 2, description_item)
            self.category_table.setItem(row, 3, status_item)
            self.category_table.setItem(row, 4, id_item)

            if category["category_id"] == selected_id:
                selected_row = row

        if selected_row >= 0:
            self.category_table.selectRow(selected_row)

        self.result_label.setText(
            f"{len(filtered)} category/categories"
        )

        self._update_buttons()

    def _filter_categories(self):
        self._display_categories(
            self.search_input.text(),
            self._selected_category_id()
        )

    # ==========================================
    # SELECTION
    # ==========================================

    def _selected_category_id(self):
        row = self.category_table.currentRow()

        if row < 0:
            return None

        item = self.category_table.item(row, 0)

        if item is None:
            return None

        return item.data(Qt.ItemDataRole.UserRole)

    def _selected_category(self):
        category_id = self._selected_category_id()

        if category_id is None:
            return None

        return next(
            (
                category for category in self.categories
                if category["category_id"] == category_id
            ),
            None
        )

    def _update_buttons(self):
        category = self._selected_category()

        self.edit_button.setEnabled(category is not None)
        self.status_button.setEnabled(category is not None)

        self.status_button.setText(
            "Deactivate"
            if category and category["is_active"]
            else "Activate"
        )

    # ==========================================
    # ADD
    # ==========================================

    def add_category(self):
        dialog = CategoryDialog(
            self.categories,
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_form_data()

        try:
            category_id = self.category_service.create_category(
                **data
            )

            self.load_categories()
            self._select_category(category_id)

            self._show_message(
                "Category Created",
                "Category created successfully."
            )

        except Exception as exc:
            self._show_message(
                "Unable to Create Category",
                str(exc),
                QMessageBox.Icon.Warning
            )

    # ==========================================
    # EDIT
    # ==========================================

    def edit_category(self):
        category = self._selected_category()

        if category is None:
            return

        dialog = CategoryDialog(
            self.categories,
            category=category,
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_form_data()

        try:
            self.category_service.update_category(
                category_id=category["category_id"],
                **data
            )

            self.load_categories()
            self._select_category(category["category_id"])

        except Exception as exc:
            self._show_message(
                "Unable to Update Category",
                str(exc),
                QMessageBox.Icon.Warning
            )

    # ==========================================
    # ACTIVATE / DEACTIVATE
    # ==========================================

    def toggle_category_status(self):
        category = self._selected_category()

        if category is None:
            return

        new_status = not bool(category["is_active"])

        action = "activate" if new_status else "deactivate"

        confirmed = self._confirm_action(
            "Confirm Category Status",
            f"Are you sure you want to {action} "
            f"'{category['category_name']}'?"
        )

        if not confirmed:
            return

        try:
            self.category_service.set_category_active(
                category["category_id"],
                new_status
            )

            self.load_categories()
            self._select_category(category["category_id"])

        except Exception as exc:
            self._show_message(
                "Unable to Change Category Status",
                str(exc),
                QMessageBox.Icon.Warning
            )

    def _select_category(self, category_id):
        for row in range(self.category_table.rowCount()):
            item = self.category_table.item(row, 0)

            if (
                item is not None
                and item.data(Qt.ItemDataRole.UserRole) == category_id
            ):
                self.category_table.selectRow(row)
                break
