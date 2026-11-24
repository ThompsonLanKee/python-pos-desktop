
from operator import index

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QFormLayout,
    QSpinBox, QPlainTextEdit, QMessageBox, QTabWidget,
    QInputDialog, QDateEdit, QFileDialog
)

from PySide6.QtGui import QColor, QBrush


STYLE = """
QWidget {
    color: #26352C;
    font-size: 13px;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTableWidget {
    background: white;
    border: 1px solid #DCE5DE;
    border-radius: 7px;
    padding: 7px;
}
QTableWidget {
    background-color: #FFFFFF;
    color: #26352C;
    alternate-background-color: #F5F8F6;
    gridline-color: #E5EAE6;
    selection-background-color: #C7E4D0;
    selection-color: #203D2E;
}
QTableWidget::item {
    color: #26352C;
    padding: 6px;
}
QTableWidget::item:selected {
    background: #C7E4D0;
    color: #203D2E;
}
QHeaderView::section {
    background: #EAF1EC;
    color: #203D2E;
    padding: 10px;
    border: none;
    font-weight: 600;
}
QTabWidget::pane {
    background-color: #F5F8F6;
    border: 1px solid #DCE5DE;
    border-radius: 7px;
    top: -1px;
}
QTabBar::tab {
    background-color: #E8F0EA;
    color: #203D2E;
    padding: 9px 16px;
    border: 1px solid #DCE5DE;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: #315F43;
    color: #FFFFFF;
    border-color: #315F43;
}
QTabBar::tab:hover:!selected {
    background-color: #D6EBDD;
}
QPushButton {
    background: #E8F0EA;
    color: #203D2E;
    border: 1px solid #C9D9CE;
    border-radius: 7px;
    padding: 9px 15px;
}
QPushButton:hover {
    background: #D6EBDD;
}
QPushButton#primary {
    background: #315F43;
    color: white;
    font-weight: 600;
}
QPushButton#primary:hover {
    background: #407653;
}
"""

DIALOG_STYLE = """
QDialog, QMessageBox {
    background-color: #F5F8F6;
    color: #203D2E;
}
QLabel {
    color: #203D2E;
    background-color: transparent;
}
QLineEdit, QSpinBox, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #203D2E;
    border: 1px solid #C9D9CE;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #C7E4D0;
    selection-color: #203D2E;
}
QPushButton {
    background-color: #E8F0EA;
    color: #203D2E;
    border: 1px solid #C9D9CE;
    border-radius: 7px;
    padding: 9px 16px;
}
QPushButton:hover {
    background-color: #D6EBDD;
}
QPushButton#primary {
    background-color: #315F43;
    color: #FFFFFF;
    border-color: #315F43;
    font-weight: 600;
}
QPushButton#primary:hover {
    background-color: #407653;
}
"""


class StockMovementDialog(QDialog):
    def __init__(self, variant, movement_type, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(DIALOG_STYLE)

        self.variant = variant
        self.movement_type = movement_type

        self.setWindowTitle(movement_type)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000000)
        self.quantity_input.setValue(1)

        self.notes_input = QPlainTextEdit()
        self.notes_input.setMaximumHeight(85)

        form.addRow("SKU:", QLabel(variant.get("sku", "")))
        form.addRow("Quantity:", self.quantity_input)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Cancel")
        save = QPushButton("Confirm")
        save.setObjectName("primary")

        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)

        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def get_data(self):
        return {
            "quantity": self.quantity_input.value(),
            "notes": self.notes_input.toPlainText().strip() or None
        }


class ReorderLevelDialog(QDialog):
    def __init__(self, current_level, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowTitle("Update Reorder Level")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.level_input = QSpinBox()
        self.level_input.setRange(0, 1000000)
        self.level_input.setValue(int(current_level or 0))

        form.addRow("Reorder Level:", self.level_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Cancel")
        save = QPushButton("Save")
        save.setObjectName("primary")

        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)

        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)


class InventoryView(QWidget):
    def __init__(self, inventory_service, parent=None):
        super().__init__(parent)

        self.inventory_service = inventory_service
        self.inventory = []
        self.transactions = []
        self.filtered_transactions = []

        self.setStyleSheet(STYLE)

        self._build_ui()
        self.load_inventory()
        
        
    def _on_tab_changed(self, index):
        if index == 1:
            self.load_transactions()

        elif index == 2:
            self.load_reports()
            
    def load_reports(self):
        try:
            inventory = self.inventory_service.get_all_inventory()

            total_units = 0
            total_cost_value = 0.0
            total_sales_value = 0.0

            self.report_table.setRowCount(len(inventory))

            for row, item in enumerate(inventory):

                quantity = int(
                    item.get("quantity_on_hand") or 0
                )

                cost_price = float(
                    item.get("cost_price") or 0
                )

                selling_price = float(
                    item.get("selling_price") or 0
                )

                cost_value = quantity * cost_price
                sales_value = quantity * selling_price

                total_units += quantity
                total_cost_value += cost_value
                total_sales_value += sales_value

                values = [
                    item.get("sku", ""),
                    item.get("product_name", ""),
                    str(quantity),
                    f"{cost_price:,.2f}",
                    f"{selling_price:,.2f}",
                    f"{cost_value:,.2f}",
                    f"{sales_value:,.2f}",
                ]

                for col, value in enumerate(values):
                    cell = QTableWidgetItem(str(value))
                    self.report_table.setItem(row, col, cell)

            potential_margin = (
                total_sales_value - total_cost_value
            )

            self.report_summary.setText(
                f"Total Units: {total_units:,}\n"
                f"Total Stock Cost Value: {total_cost_value:,.2f} MMK\n"
                f"Potential Sales Value: {total_sales_value:,.2f} MMK\n"
                f"Potential Gross Margin: {potential_margin:,.2f} MMK"
            )

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Report Error",
                str(exc)
            )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 5, 0, 0)
        root.setSpacing(14)

        heading = QLabel("Inventory Management")
        heading.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #203D2E;"
        )
        root.addWidget(heading)

        description = QLabel(
            "Monitor stock levels and record inventory movements."
        )
        description.setStyleSheet("color: #829087;")
        root.addWidget(description)

        # Summary cards
        cards = QGridLayout()
        cards.setSpacing(12)

        self.total_label = self._create_card(
            cards, 0, "Inventory Items"
        )
        self.low_label = self._create_card(
            cards, 1, "Low Stock"
        )
        self.out_label = self._create_card(
            cards, 2, "Out of Stock"
        )

        root.addLayout(cards)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Stock overview
        overview = QWidget()
        overview.setObjectName("inventory_overview")
        overview.setStyleSheet(
            "#inventory_overview { background-color: #F5F8F6; }"
        )
        overview_layout = QVBoxLayout(overview)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search product, SKU, barcode..."
        )
        self.search_input.textChanged.connect(
            self.load_inventory
        )

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Stock", "all")
        self.filter_combo.addItem("Low Stock", "low")
        self.filter_combo.addItem("Out of Stock", "out")
        self.filter_combo.currentIndexChanged.connect(
            self.load_inventory
        )

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_all)

        self.reorder_button = QPushButton("Reorder Level")
        self.reorder_button.clicked.connect(
            self.update_reorder_level
        )

        export_stock = QPushButton("Export Excel")
        export_stock.setObjectName("primary")
        export_stock.clicked.connect(self.export_stock_excel)

        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(self.reorder_button)
        toolbar.addWidget(export_stock)
        toolbar.addWidget(refresh)

        overview_layout.addLayout(toolbar)

        self.stock_table = self._create_table([
            "SKU", "Product", "Color", "Size",
            "Quantity", "Reorder Level", "Status"
        ])

        overview_layout.addWidget(self.stock_table)

        movement_buttons = QHBoxLayout()

        for label, action in [
            ("Receive Stock", "receive"),
            ("Issue Stock", "issue"),
            ("Adjust Stock", "adjust"),
            ("Record Damage", "damage"),
        ]:
            button = QPushButton(label)
            button.setObjectName(
                "primary" if action == "receive" else ""
            )
            button.clicked.connect(
                lambda checked=False, a=action:
                    self.perform_movement(a)
            )
            movement_buttons.addWidget(button)

        movement_buttons.addStretch()
        overview_layout.addLayout(movement_buttons)

        self.tabs.addTab(overview, "Stock Overview")

        # Movement history
        history = QWidget()
        history.setObjectName("inventory_history")
        history.setStyleSheet(
            "#inventory_history { background-color: #F5F8F6; }"
        )
        history_layout = QVBoxLayout(history)

        # Movement history filters
        history_filters = QGridLayout()
        history_filters.setHorizontalSpacing(8)
        history_filters.setVerticalSpacing(8)

        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search SKU or product...")
        self.history_search.textChanged.connect(self._apply_history_filters)

        self.movement_type_filter = QComboBox()
        self.movement_type_filter.addItem("All Movement Types", "all")
        for movement_type in (
            "PURCHASE", "SALE", "ADJUSTMENT_IN",
            "ADJUSTMENT_OUT", "DAMAGE"
        ):
            self.movement_type_filter.addItem(movement_type, movement_type)
        self.movement_type_filter.currentIndexChanged.connect(
            self._apply_history_filters
        )

        self.history_start_date = QDateEdit()
        self.history_start_date.setCalendarPopup(True)
        self.history_start_date.setDisplayFormat("yyyy-MM-dd")
        self.history_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.history_start_date.dateChanged.connect(
            self._apply_history_filters
        )

        self.history_end_date = QDateEdit()
        self.history_end_date.setCalendarPopup(True)
        self.history_end_date.setDisplayFormat("yyyy-MM-dd")
        self.history_end_date.setDate(QDate.currentDate())
        self.history_end_date.dateChanged.connect(
            self._apply_history_filters
        )

        history_refresh = QPushButton("Refresh")
        history_refresh.clicked.connect(self.load_transactions)

        reset_filters = QPushButton("Reset Filters")
        reset_filters.clicked.connect(self.reset_history_filters)

        export_history = QPushButton("Export Excel")
        export_history.setObjectName("primary")
        export_history.clicked.connect(self.export_history_excel)

        history_filters.addWidget(self.history_search, 0, 0, 1, 2)
        history_filters.addWidget(QLabel("Movement:"), 0, 2)
        history_filters.addWidget(self.movement_type_filter, 0, 3)
        history_filters.addWidget(QLabel("From:"), 1, 0)
        history_filters.addWidget(self.history_start_date, 1, 1)
        history_filters.addWidget(QLabel("To:"), 1, 2)
        history_filters.addWidget(self.history_end_date, 1, 3)
        history_filters.addWidget(reset_filters, 0, 4)
        history_filters.addWidget(history_refresh, 1, 4)
        history_filters.addWidget(export_history, 0, 5, 2, 1)

        history_layout.addLayout(history_filters)

        self.history_count_label = QLabel("0 movements")
        self.history_count_label.setStyleSheet("color: #718078;")
        history_layout.addWidget(self.history_count_label)

        self.history_table = self._create_table([
            "Date",
            "SKU",
            "Product",
            "Movement Type",
            "Quantity Change",
            "Balance After",
            "Notes"
        ])

        history_layout.addWidget(self.history_table)

        self.tabs.addTab(history, "Movement History")
        
        # Inventory Reports
        reports = QWidget()
        reports_layout = QVBoxLayout(reports)

        report_heading = QLabel("Inventory Valuation")
        report_heading.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #203D2E;"
        )

        report_description = QLabel(
            "View current stock quantities and estimated inventory values."
        )

        reports_layout.addWidget(report_heading)
        reports_layout.addWidget(report_description)

        self.report_summary = QLabel()
        self.report_summary.setStyleSheet("""
            background: #EAF1EC;
            border: 1px solid #DCE5DE;
            border-radius: 8px;
            padding: 15px;
            font-size: 14px;
            color: #203D2E;
        """)
        reports_layout.addWidget(self.report_summary)

        self.report_table = self._create_table([
            "SKU",
            "Product",
            "Quantity",
            "Cost Price",
            "Selling Price",
            "Stock Cost Value",
            "Potential Sales Value"
        ])

        reports_layout.addWidget(self.report_table)

        report_refresh = QPushButton("Refresh Reports")
        report_refresh.clicked.connect(self.load_reports)
        reports_layout.addWidget(report_refresh)

        self.tabs.addTab(reports, "Inventory Reports")
        
        self.tabs.currentChanged.connect(
        self._on_tab_changed
        )

    def _create_card(self, grid, column, title):
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background: #EAF1EC;
                border: 1px solid #DCE5DE;
                border-radius: 9px;
            }
        """)

        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "border: none; color: #718078;"
        )

        value_label = QLabel("0")
        value_label.setStyleSheet(
            "border: none; font-size: 23px; "
            "font-weight: 700; color: #315F43;"
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        grid.addWidget(card, 0, column)
        return value_label

    @staticmethod
    def _create_table(headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)

        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.horizontalHeader().setMinimumHeight(40)

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                color: #26352C;
                selection-background-color: #C7E4D0;
                selection-color: #203D2E;
                alternate-background-color: #F5F8F6;
                gridline-color: #DCE5DE;
                border: 1px solid #DCE5DE;
                border-radius: 7px;
            }

            QTableWidget::item {
                color: #26352C;
                padding: 6px;
            }

            QTableWidget::item:selected {
                background-color: #B5DCC1;
                color: #203D2E;
                border: 1px solid #76A986;
            }

            QTableWidget::item:selected:!active {
                background-color: #C7E4D0;
                color: #203D2E;
            }

            QHeaderView::section {
                background-color: #EAF1EC;
                color: #203D2E;
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid #DCE5DE;
                font-weight: 600;
            }
        """)

        table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        table.setShowGrid(True)

        return table

    def _show_message(self, icon, title, text):
        message_box = QMessageBox(self)
        message_box.setIcon(icon)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.setMinimumWidth(380)
        message_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        message_box.setStyleSheet(DIALOG_STYLE)
        message_box.exec()

    def load_inventory(self, *_):
        try:
            self.inventory = self.inventory_service.get_all_inventory()

            keyword = self.search_input.text().strip().lower()
            filter_type = self.filter_combo.currentData()

            rows = []

            for item in self.inventory:
                searchable = " ".join(
                    str(item.get(key, "") or "")
                    for key in (
                        "sku", "barcode", "product_name",
                        "color_name", "size_name"
                    )
                ).lower()

                if keyword and keyword not in searchable:
                    continue

                quantity = int(item.get("quantity_on_hand") or 0)
                reorder = int(item.get("reorder_level") or 0)

                if filter_type == "low" and not (
                    quantity > 0 and quantity <= reorder
                ):
                    continue

                if filter_type == "out" and quantity != 0:
                    continue

                rows.append(item)

            low_count = sum(
                1 for item in self.inventory
                if 0 < int(item.get("quantity_on_hand") or 0)
                <= int(item.get("reorder_level") or 0)
            )

            out_count = sum(
                1 for item in self.inventory
                if int(item.get("quantity_on_hand") or 0) == 0
            )

            self.total_label.setText(str(len(self.inventory)))
            self.low_label.setText(str(low_count))
            self.out_label.setText(str(out_count))

            self.stock_table.setRowCount(len(rows))

            for row, item in enumerate(rows):
                quantity = int(item.get("quantity_on_hand") or 0)
                reorder = int(item.get("reorder_level") or 0)

                status = (
                    "Out of Stock" if quantity == 0
                    else "Low Stock" if quantity <= reorder
                    else "In Stock"
                )

                values = [
                    item.get("sku", ""),
                    item.get("product_name", ""),
                    item.get("color_name") or "—",
                    item.get("size_name") or "—",
                    str(quantity),
                    str(reorder),
                    status,
                ]

                for col, value in enumerate(values):
                    cell = QTableWidgetItem(str(value))

                    if col == 0:
                        cell.setData(
                            Qt.ItemDataRole.UserRole,
                            item.get("variant_id")
                        )

                    if col == 6:
                        if status == "In Stock":
                            cell.setForeground(QBrush(QColor("#237A43")))
                            cell.setBackground(QBrush(QColor("#E2F2E6")))

                        elif status == "Low Stock":
                            cell.setForeground(QBrush(QColor("#9A6700")))
                            cell.setBackground(QBrush(QColor("#FFF3CD")))

                        else:
                            cell.setForeground(QBrush(QColor("#B42318")))
                            cell.setBackground(QBrush(QColor("#FDE8E7")))

                    self.stock_table.setItem(row, col, cell)

        except Exception as exc:
            self._show_message(
                QMessageBox.Icon.Critical,
                "Inventory Error",
                f"Unable to load inventory:\n{exc}"
            )

    def export_stock_excel(self):
        """Export the currently filtered stock overview to an XLSX file."""
        keyword = self.search_input.text().strip().lower()
        filter_type = self.filter_combo.currentData()

        rows = []
        for item in self.inventory:
            searchable = " ".join(
                str(item.get(key, "") or "")
                for key in (
                    "sku", "barcode", "product_name",
                    "color_name", "size_name"
                )
            ).lower()

            if keyword and keyword not in searchable:
                continue

            quantity = int(item.get("quantity_on_hand") or 0)
            reorder = int(item.get("reorder_level") or 0)

            if filter_type == "low" and not (
                quantity > 0 and quantity <= reorder
            ):
                continue

            if filter_type == "out" and quantity != 0:
                continue

            status = (
                "Out of Stock" if quantity == 0
                else "Low Stock" if quantity <= reorder
                else "In Stock"
            )

            rows.append((item, quantity, reorder, status))

        if not rows:
            self._show_message(
                QMessageBox.Icon.Information,
                "Nothing to Export",
                "There are no stock records matching the current filters."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Stock Overview",
            "inventory_stock_overview.xlsx",
            "Excel Workbook (*.xlsx)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Stock Overview"

            headers = [
                "SKU", "Barcode", "Product", "Color", "Size",
                "Quantity", "Reorder Level", "Cost Price",
                "Selling Price", "Stock Cost Value", "Status"
            ]
            sheet.append(headers)

            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(
                    fill_type="solid", fgColor="315F43"
                )
                cell.alignment = Alignment(horizontal="center")

            for item, quantity, reorder, status in rows:
                cost_price = float(item.get("cost_price") or 0)
                selling_price = float(item.get("selling_price") or 0)

                sheet.append([
                    item.get("sku", ""),
                    item.get("barcode", "") or "",
                    item.get("product_name", ""),
                    item.get("color_name", "") or "",
                    item.get("size_name", "") or "",
                    quantity,
                    reorder,
                    cost_price,
                    selling_price,
                    quantity * cost_price,
                    status,
                ])

            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    if cell.column in (8, 9, 10):
                        cell.number_format = '#,##0.00'
                status_cell = row[10]
                if status_cell.value == "In Stock":
                    status_cell.font = Font(color="237A43", bold=True)
                elif status_cell.value == "Low Stock":
                    status_cell.font = Font(color="9A6700", bold=True)
                else:
                    status_cell.font = Font(color="B42318", bold=True)

            for column_cells in sheet.columns:
                max_length = max(
                    len(str(cell.value or "")) for cell in column_cells
                )
                sheet.column_dimensions[
                    get_column_letter(column_cells[0].column)
                ].width = min(max(max_length + 3, 14), 34)

            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            workbook.save(file_path)

            self._show_message(
                QMessageBox.Icon.Information,
                "Export Complete",
                f"Stock overview exported successfully:\n{file_path}"
            )

        except ImportError:
            self._show_message(
                QMessageBox.Icon.Warning,
                "Excel Library Missing",
                "Install openpyxl using:\npython -m pip install openpyxl"
            )
        except Exception as exc:
            self._show_message(
                QMessageBox.Icon.Critical,
                "Export Failed",
                str(exc)
            )

    def _selected_item(self):
        row = self.stock_table.currentRow()

        if row < 0:
            self._show_message(
                QMessageBox.Icon.Warning,
                "Select Item",
                "Please click an inventory row to select an item first."
            )
            return None

        cell = self.stock_table.item(row, 0)

        if cell is None:
            return None

        variant_id = cell.data(Qt.ItemDataRole.UserRole)

        if variant_id is None:
            return None

        return next(
            (
                item for item in self.inventory
                if int(item.get("variant_id", 0)) == int(variant_id)
            ),
            None
        )

    def perform_movement(self, action):
        item = self._selected_item()

        if not item:
            return

        titles = {
            "receive": "Receive Stock",
            "issue": "Issue Stock",
            "adjust": "Adjust Stock",
            "damage": "Record Damaged Stock",
        }

        dialog = StockMovementDialog(
            item, titles[action], self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        quantity = data["quantity"]
        notes = data["notes"]
        variant_id = item["variant_id"]

        try:
            if action == "receive":
                result = self.inventory_service.receive_stock(
                    variant_id, quantity, notes=notes
                )

            elif action == "issue":
                result = self.inventory_service.issue_stock(
                    variant_id, quantity, notes=notes
                )

            elif action == "adjust":
                direction, ok = self._adjustment_direction()
                if not ok:
                    return

                change = quantity if direction == "in" else -quantity

                result = self.inventory_service.adjust_stock(
                    variant_id, change, notes=notes
                )

            else:
                result = self.inventory_service.record_damage(
                    variant_id, quantity, notes=notes
                )

            if result:
                self._show_message(
                    QMessageBox.Icon.Information,
                    "Success",
                    "Inventory movement recorded successfully."
                )

            self.refresh_all()

        except Exception as exc:
            self._show_message(
                QMessageBox.Icon.Warning,
                "Movement Failed",
                str(exc)
            )

    def _adjustment_direction(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Adjustment Direction")
        dialog.setLabelText("Select adjustment type:")
        dialog.setComboBoxItems(["Increase (+)", "Decrease (-)"])
        dialog.setComboBoxEditable(False)
        dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dialog.setAutoFillBackground(True)
        dialog.setStyleSheet(DIALOG_STYLE)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None, False

        direction = dialog.textValue()
        return ("in" if direction.startswith("Increase") else "out"), True

    def update_reorder_level(self):
        item = self._selected_item()

        if not item:
            return

        dialog = ReorderLevelDialog(
            item.get("reorder_level", 0), self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            result = self.inventory_service.set_reorder_level(
                item["variant_id"],
                dialog.level_input.value()
            )

            if result:
                self._show_message(
                    QMessageBox.Icon.Information,
                    "Success",
                    "Reorder level updated."
                )

            self.refresh_all()

        except Exception as exc:
            self._show_message(
                QMessageBox.Icon.Warning,
                "Update Failed",
                str(exc)
            )

    def load_transactions(self):
        try:
            self.transactions = (
                self.inventory_service.get_all_transactions()
            )
            self._apply_history_filters()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "History Error",
                str(exc)
            )

    def _apply_history_filters(self, *_):
        """Filter movement history using search, type and date range."""
        keyword = self.history_search.text().strip().lower()
        movement_type = self.movement_type_filter.currentData()
        start_date = self.history_start_date.date().toString("yyyy-MM-dd")
        end_date = self.history_end_date.date().toString("yyyy-MM-dd")

        if start_date > end_date:
            self.history_count_label.setText(
                "Invalid date range: start date is after end date."
            )
            self.history_table.setRowCount(0)
            self.filtered_transactions = []
            return

        filtered = []
        for item in self.transactions:
            created_at = str(item.get("created_at") or "")
            movement_date = created_at[:10]

            searchable = " ".join(
                str(item.get(key) or "")
                for key in ("sku", "product_name", "notes", "reference_type")
            ).lower()

            if keyword and keyword not in searchable:
                continue
            if movement_type != "all" and item.get("transaction_type") != movement_type:
                continue
            if not movement_date or not (start_date <= movement_date <= end_date):
                continue

            filtered.append(item)

        self.filtered_transactions = filtered
        self.history_table.setRowCount(len(filtered))

        for row, item in enumerate(filtered):
            quantity_change = int(item.get("quantity_change") or 0)
            quantity_text = (
                f"+{quantity_change}" if quantity_change > 0
                else str(quantity_change)
            )

            values = [
                item.get("created_at", ""),
                item.get("sku", ""),
                item.get("product_name", ""),
                item.get("transaction_type", ""),
                quantity_text,
                str(item.get("quantity_after", "")),
                item.get("notes") or "—",
            ]

            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))

                if col == 4:
                    if quantity_change > 0:
                        cell.setForeground(QBrush(QColor("#237A43")))
                    elif quantity_change < 0:
                        cell.setForeground(QBrush(QColor("#B42318")))

                if col == 3:
                    cell.setForeground(QBrush(QColor("#315F43")))

                self.history_table.setItem(row, col, cell)

        self.history_count_label.setText(
            f"Showing {len(filtered):,} of {len(self.transactions):,} movements"
        )

    def reset_history_filters(self):
        self.history_search.clear()
        self.movement_type_filter.setCurrentIndex(0)
        self.history_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.history_end_date.setDate(QDate.currentDate())
        self._apply_history_filters()

    def export_history_excel(self):
        """Export the currently filtered movement history to an XLSX file."""
        if not self.filtered_transactions:
            self._show_message(
                QMessageBox.Icon.Information,
                "Nothing to Export",
                "There are no movement records matching the current filters."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Movement History",
            "inventory_movement_history.xlsx",
            "Excel Workbook (*.xlsx)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Movement History"

            headers = [
                "Transaction Date", "SKU", "Product", "Movement Type",
                "Quantity Change", "Balance After", "Reference Type",
                "Reference ID", "Notes"
            ]
            sheet.append(headers)

            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(
                    fill_type="solid", fgColor="315F43"
                )
                cell.alignment = Alignment(horizontal="center")

            for item in self.filtered_transactions:
                sheet.append([
                    item.get("created_at", ""),
                    item.get("sku", ""),
                    item.get("product_name", ""),
                    item.get("transaction_type", ""),
                    int(item.get("quantity_change") or 0),
                    int(item.get("quantity_after") or 0),
                    item.get("reference_type") or "",
                    item.get("reference_id") or "",
                    item.get("notes") or "",
                ])

            for column_cells in sheet.columns:
                max_length = max(
                    len(str(cell.value or "")) for cell in column_cells
                )
                sheet.column_dimensions[
                    get_column_letter(column_cells[0].column)
                ].width = min(max(max_length + 3, 14), 36)

            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            workbook.save(file_path)

            self._show_message(
                QMessageBox.Icon.Information,
                "Export Complete",
                f"Movement history exported successfully to:\n{file_path}"
            )

        except ImportError:
            self._show_message(
                QMessageBox.Icon.Warning,
                "Excel Library Missing",
                "Install openpyxl first using:\npython -m pip install openpyxl"
            )
        except Exception as exc:
            self._show_message(
                QMessageBox.Icon.Critical,
                "Export Failed",
                str(exc)
            )

    def refresh_all(self):
        self.load_inventory()
        self.load_transactions()
