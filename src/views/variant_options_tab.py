
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QSpinBox, QMessageBox, QAbstractItemView, QTabWidget,
    QColorDialog
)

from src.models import Color, Size


class OptionDialog(QDialog):
    """Add or edit a color or size."""

    def __init__(self, option_type, option=None, parent=None):
        super().__init__(parent)

        self.option_type = option_type
        self.option = option

        self.setWindowTitle(
            f"{'Edit' if option else 'Add'} {option_type.title()}"
        )
        self.setMinimumWidth(400)

        self.name_input = QLineEdit()
        self.name_input.setMaxLength(80)

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("#FFFFFF")

        self.order_input = QSpinBox()
        self.order_input.setRange(0, 9999)

        form = QFormLayout()
        form.addRow(f"{option_type.title()} Name *", self.name_input)

        if option_type == "color":
            color_input = QWidget()
            color_input_layout = QHBoxLayout(color_input)
            color_input_layout.setContentsMargins(0, 0, 0, 0)
            color_input_layout.setSpacing(8)

            self.color_picker_button = QPushButton("Pick Color")
            self.color_picker_button.clicked.connect(self._choose_color)
            color_input_layout.addWidget(self.hex_input, 1)
            color_input_layout.addWidget(self.color_picker_button)

            form.addRow("Hex Code", color_input)
        else:
            form.addRow("Sort Order", self.order_input)

        save_button = QPushButton("Save")
        save_button.setObjectName("primary_button")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

        if option:
            self.name_input.setText(
                option.color_name if option_type == "color"
                else option.size_name
            )

            if option_type == "color":
                self.hex_input.setText(option.hex_code or "")
            else:
                self.order_input.setValue(option.sort_order)

    def _choose_color(self):
        current_color = QColor(self.hex_input.text().strip())
        if not current_color.isValid():
            current_color = QColor("#FFFFFF")

        selected_color = QColorDialog.getColor(
            current_color,
            self,
            "Choose Color",
            options=QColorDialog.ColorDialogOption.DontUseNativeDialog,
        )
        if selected_color.isValid():
            self.hex_input.setText(
                selected_color.name(QColor.NameFormat.HexRgb).upper()
            )

    def get_data(self):
        name = self.name_input.text().strip()

        if not name:
            raise ValueError("Name cannot be empty.")

        if self.option_type == "color":
            hex_code = self.hex_input.text().strip().upper()

            if hex_code and (
                len(hex_code) != 7
                or not hex_code.startswith("#")
                or any(c not in "0123456789ABCDEF" for c in hex_code[1:])
            ):
                raise ValueError("Enter a valid hex code, e.g. #FFFFFF.")

            return Color(
                color_id=self.option.color_id if self.option else None,
                color_name=name,
                hex_code=hex_code or None,
                is_active=self.option.is_active if self.option else True
            )

        return Size(
            size_id=self.option.size_id if self.option else None,
            size_name=name,
            sort_order=self.order_input.value(),
            is_active=self.option.is_active if self.option else True
        )


class VariantOptionsTab(QWidget):
    """Manage colors and sizes used by product variants."""

    def __init__(self, database, parent=None):
        super().__init__(parent)

        self.database = database
        self.current_type = "color"

        self.setStyleSheet("""
            QWidget {
                color: #203D2E;
                font-size: 13px;
            }
            QLineEdit, QSpinBox, QTableWidget {
                background: #FFFFFF;
                color: #203D2E;
                border: 1px solid #C8D8CD;
                border-radius: 6px;
                padding: 7px;
            }
            QHeaderView::section {
                background: #EAF1EC;
                color: #203D2E;
                padding: 9px;
                border: none;
                font-weight: 600;
            }
            QPushButton {
                background: #E6EEE8;
                color: #203D2E;
                border: 1px solid #C8D8CD;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton#primary_button {
                background: #315D40;
                color: white;
                border: none;
                font-weight: 600;
            }
            QPushButton#primary_button:hover {
                background: #43845A;
            }
            QTableWidget {
                gridline-color: #E5EAE6;
                alternate-background-color: #F5F8F6;
                selection-background-color: #D6EBDD;
                selection-color: #203D2E;
            }
        """)

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        heading = QLabel("Variant Options")
        heading.setObjectName("section_title")

        subtitle = QLabel(
            "Manage colors and sizes available when creating product variants."
        )
        subtitle.setObjectName("page_subtitle")

        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.option_tabs = QTabWidget()
        self.option_tabs.addTab(QWidget(), "Colors")
        self.option_tabs.addTab(QWidget(), "Sizes")
        self.option_tabs.currentChanged.connect(self._tab_changed)

        layout.addWidget(self.option_tabs)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.load_data)

        self.add_button = QPushButton("Add")
        self.add_button.setObjectName("primary_button")
        self.add_button.clicked.connect(self.add_option)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_option)

        self.status_button = QPushButton("Deactivate")
        self.status_button.clicked.connect(self.toggle_status)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)

        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.status_button)
        toolbar.addWidget(self.refresh_button)

        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.itemSelectionChanged.connect(
            self._update_buttons
        )
        
        self.table.setStyleSheet("""
            QTableWidget {
            gridline-color: #E5EAE6;
            alternate-background-color: #F5F8F6;
            selection-background-color: #D6EBDD;
            selection-color: #203D2E;
        }

        QTableWidget::item:selected {
            background-color: #D6EBDD;
            color: #203D2E;
        }

        QTableWidget::item:selected:!active {
            background-color: #D6EBDD;
            color: #203D2E;
        }
     """)

        layout.addWidget(self.table, 1)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self._configure_columns()

    def _tab_changed(self, index):
        self.current_type = "color" if index == 0 else "size"
        self.search_input.clear()
        self._configure_columns()
        self.load_data()

    def _configure_columns(self):
        if self.current_type == "color":
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels([
                "Color Name", "Hex Code", "Preview", "Status"
            ])
        else:
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels([
                "Size Name", "Sort Order", "Status"
            ])

    def load_data(self):
        keyword = self.search_input.text().strip().lower()

        try:
            with self.database.connect() as connection:
                if self.current_type == "color":
                    rows = connection.execute("""
                        SELECT color_id, color_name, hex_code, is_active
                        FROM colors
                        ORDER BY color_name
                    """).fetchall()
                else:
                    rows = connection.execute("""
                        SELECT size_id, size_name, sort_order, is_active
                        FROM sizes
                        ORDER BY sort_order, size_name
                    """).fetchall()

            self.table.setRowCount(0)

            for row in rows:
                data = dict(row)
                name = (
                    data["color_name"]
                    if self.current_type == "color"
                    else data["size_name"]
                )

                if keyword and keyword not in name.lower():
                    continue

                index = self.table.rowCount()
                self.table.insertRow(index)

                if self.current_type == "color":
                    values = [
                        name,
                        data["hex_code"] or "-",
                        "",
                        "Active" if data["is_active"] else "Inactive"
                    ]
                else:
                    values = [
                        name,
                        str(data["sort_order"]),
                        "Active" if data["is_active"] else "Inactive"
                    ]

                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        data["color_id"] if self.current_type == "color"
                        else data["size_id"]
                    )
                    self.table.setItem(index, column, item)

                if self.current_type == "color":
                    hex_code = data["hex_code"] or "#B8C4BC"

                    color = QColor(hex_code)
                    if not color.isValid():
                        color = QColor("#B8C4BC")

                    preview_container = QWidget()
                    preview_layout = QHBoxLayout(preview_container)
                    preview_layout.setContentsMargins(0, 0, 0, 0)
                    preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    sphere = QLabel()
                    sphere.setFixedSize(24, 24)
                    sphere.setStyleSheet(f"""
                        background-color: {color.name()};
                        border: 1px solid #AAB8AE;
                        border-radius: 12px;
                    """)
                    sphere.setToolTip(hex_code)

                    preview_layout.addWidget(sphere)

                    self.table.setCellWidget(index, 2, preview_container)
                    self.table.setRowHeight(index, 42)

            self.status_label.setText(
                f"{self.table.rowCount()} record(s)"
            )
            self._update_buttons()

        except Exception as exc:
            QMessageBox.critical(
                self, "Load Error", str(exc)
            )

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _selected_option(self):
        option_id = self._selected_id()
        if option_id is None:
            return None

        table = "colors" if self.current_type == "color" else "sizes"
        id_column = "color_id" if self.current_type == "color" else "size_id"

        with self.database.connect() as connection:
            row = connection.execute(
                f"SELECT * FROM {table} WHERE {id_column} = ?",
                (option_id,)
            ).fetchone()

        if row is None:
            return None

        if self.current_type == "color":
            return Color(**dict(row))
        return Size(**dict(row))

    def _update_buttons(self):
        option = self._selected_option()
        self.edit_button.setEnabled(option is not None)
        self.status_button.setEnabled(option is not None)

        if option:
            self.status_button.setText(
                "Deactivate" if option.is_active else "Activate"
            )
        else:
            self.status_button.setText("Deactivate")

    def add_option(self):
        self._open_dialog()

    def edit_option(self):
        option = self._selected_option()
        if option:
            self._open_dialog(option)

    def _open_dialog(self, option=None):
        dialog = OptionDialog(
            self.current_type,
            option,
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            model = dialog.get_data()

            with self.database.connect() as connection:
                if self.current_type == "color":
                    if option:
                        connection.execute("""
                            UPDATE colors
                            SET color_name = ?, hex_code = ?
                            WHERE color_id = ?
                        """, (
                            model.color_name,
                            model.hex_code,
                            model.color_id
                        ))
                    else:
                        connection.execute("""
                            INSERT INTO colors (
                                color_name, hex_code, is_active
                            )
                            VALUES (?, ?, ?)
                        """, (
                            model.color_name,
                            model.hex_code,
                            int(model.is_active)
                        ))
                else:
                    if option:
                        connection.execute("""
                            UPDATE sizes
                            SET size_name = ?, sort_order = ?
                            WHERE size_id = ?
                        """, (
                            model.size_name,
                            model.sort_order,
                            model.size_id
                        ))
                    else:
                        connection.execute("""
                            INSERT INTO sizes (
                                size_name, sort_order, is_active
                            )
                            VALUES (?, ?, ?)
                        """, (
                            model.size_name,
                            model.sort_order,
                            int(model.is_active)
                        ))

            self.load_data()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Save Error",
                f"Could not save this option:\n{exc}"
            )

    def toggle_status(self):
        option_id = self._selected_id()
        option = self._selected_option()

        if option_id is None or option is None:
            return

        new_status = not option.is_active
        action = "activate" if new_status else "deactivate"

        confirmation = QMessageBox.question(
            self,
            "Confirm Status Change",
            f"Do you want to {action} this {self.current_type}?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        table = "colors" if self.current_type == "color" else "sizes"
        id_column = "color_id" if self.current_type == "color" else "size_id"

        try:
            with self.database.connect() as connection:
                connection.execute(
                    f"UPDATE {table} SET is_active = ? WHERE {id_column} = ?",
                    (int(new_status), option_id)
                )

            self.load_data()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Status Error",
                str(exc)
            )
