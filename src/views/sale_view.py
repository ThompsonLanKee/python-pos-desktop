
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QHeaderView,
    QMessageBox,
)


class SaleView(QWidget):
    """Point of Sale screen."""

    checkout_requested = Signal()
    product_search_requested = Signal(str)

    def __init__(self, sale_service=None, parent=None):
        super().__init__(parent)

        self.sale_service = sale_service
        self.cart_items = []

        self._build_ui()
        self._apply_styles()

    # ==========================================
    # MAIN UI
    # ==========================================

    def _build_ui(self):

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.setSpacing(18)

        # Left: Product selection
        product_panel = self._build_product_panel()

        # Right: Shopping cart
        cart_panel = self._build_cart_panel()

        main_layout.addWidget(product_panel, 3)
        main_layout.addWidget(cart_panel, 2)

    # ==========================================
    # PRODUCT PANEL
    # ==========================================

    def _build_product_panel(self):

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        heading = QLabel("Products")
        heading.setObjectName("section_title")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by product name, SKU or barcode..."
        )
        self.search_input.setMinimumHeight(42)

        self.search_input.returnPressed.connect(
            self._search_products
        )

        self.product_table = QTableWidget(0, 5)
        self.product_table.setHorizontalHeaderLabels([
            "Product",
            "SKU",
            "Variant",
            "Price",
            "Stock",
        ])

        self.product_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.product_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.product_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.product_table.setAlternatingRowColors(True)

        self.add_button = QPushButton("Add to Cart")
        self.add_button.setObjectName("primary_button")
        self.add_button.setMinimumHeight(42)

        self.add_button.clicked.connect(
            self._add_selected_product
        )

        layout.addWidget(heading)
        layout.addWidget(self.search_input)
        layout.addWidget(self.product_table)
        layout.addWidget(self.add_button)

        return panel

    # ==========================================
    # CART PANEL
    # ==========================================

    def _build_cart_panel(self):

        panel = QFrame()
        panel.setObjectName("cart_panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        heading = QLabel("Current Sale")
        heading.setObjectName("section_title")

        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels([
            "Item",
            "Qty",
            "Price",
            "Total",
        ])

        self.cart_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.cart_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.cart_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # Cart actions
        action_layout = QHBoxLayout()

        self.remove_button = QPushButton("Remove Item")
        self.clear_button = QPushButton("Clear Cart")

        self.remove_button.clicked.connect(
            self._remove_selected_item
        )

        self.clear_button.clicked.connect(
            self._clear_cart
        )

        action_layout.addWidget(self.remove_button)
        action_layout.addWidget(self.clear_button)

        # Summary
        summary = QFrame()
        summary_layout = QGridLayout(summary)

        self.subtotal_label = QLabel("0 MMK")
        self.discount_label = QLabel("0 MMK")
        self.tax_label = QLabel("0 MMK")

        self.total_label = QLabel("0 MMK")
        self.total_label.setObjectName("total_value")

        summary_layout.addWidget(QLabel("Subtotal"), 0, 0)
        summary_layout.addWidget(self.subtotal_label, 0, 1)

        summary_layout.addWidget(QLabel("Discount"), 1, 0)
        summary_layout.addWidget(self.discount_label, 1, 1)

        summary_layout.addWidget(QLabel("Tax"), 2, 0)
        summary_layout.addWidget(self.tax_label, 2, 1)

        summary_layout.addWidget(QLabel("Total"), 3, 0)
        summary_layout.addWidget(self.total_label, 3, 1)

        # Checkout
        self.checkout_button = QPushButton(
            "Proceed to Checkout"
        )
        self.checkout_button.setObjectName("primary_button")
        self.checkout_button.setMinimumHeight(48)

        self.checkout_button.clicked.connect(
            self.checkout_requested.emit
        )

        layout.addWidget(heading)
        layout.addWidget(self.cart_table)
        layout.addLayout(action_layout)
        layout.addWidget(summary)
        layout.addWidget(self.checkout_button)

        return panel

    # ==========================================
    # PRODUCT SEARCH
    # ==========================================

    def _search_products(self):

        keyword = self.search_input.text().strip()

        if not keyword:
            return

        self.product_search_requested.emit(keyword)

    # ==========================================
    # CART OPERATIONS
    # ==========================================

    def _add_selected_product(self):

        row = self.product_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "No Product Selected",
                "Please select a product first."
            )
            return

        QMessageBox.information(
            self,
            "Product Selection",
            "Product selection will be connected "
            "to the inventory service next."
        )

    def _remove_selected_item(self):

        row = self.cart_table.currentRow()

        if row < 0:
            return

        if row < len(self.cart_items):
            self.cart_items.pop(row)

        self._refresh_cart()

    def _clear_cart(self):

        self.cart_items.clear()
        self._refresh_cart()

    # ==========================================
    # CART DISPLAY
    # ==========================================

    def _refresh_cart(self):

        self.cart_table.setRowCount(len(self.cart_items))

        for row, item in enumerate(self.cart_items):

            self.cart_table.setItem(
                row, 0,
                QTableWidgetItem(item["name"])
            )

            self.cart_table.setItem(
                row, 1,
                QTableWidgetItem(str(item["quantity"]))
            )

            self.cart_table.setItem(
                row, 2,
                QTableWidgetItem(f'{item["price"]:,}')
            )

            self.cart_table.setItem(
                row, 3,
                QTableWidgetItem(f'{item["total"]:,}')
            )

        subtotal = sum(
            item["total"] for item in self.cart_items
        )

        self.subtotal_label.setText(f"{subtotal:,} MMK")
        self.discount_label.setText("0 MMK")
        self.tax_label.setText("0 MMK")
        self.total_label.setText(f"{subtotal:,} MMK")

    # ==========================================
    # STYLING
    # ==========================================

    def _apply_styles(self):

        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #DCE5DE;
                border-radius: 7px;
                padding: 10px;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E5EAE6;
                border-radius: 7px;
                gridline-color: #EDF0ED;
            }

            QHeaderView::section {
                background-color: #EAF1EC;
                color: #315D40;
                padding: 9px;
                border: none;
                font-weight: bold;
            }

            #cart_panel {
                background-color: white;
                border: 1px solid #E5EAE6;
                border-radius: 10px;
            }

            #primary_button {
                background-color: #315D40;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px;
                font-weight: bold;
            }

            #primary_button:hover {
                background-color: #3F7653;
            }

            #total_value {
                color: #203D2E;
                font-size: 20px;
                font-weight: bold;
            }

            QPushButton {
                padding: 8px;
                border-radius: 6px;
            }
        """)
