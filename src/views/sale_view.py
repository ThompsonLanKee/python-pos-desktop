
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QImageReader, QPixmap

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
    QAbstractItemView,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
)


class SaleView(QWidget):
    """Point of Sale screen."""

    checkout_requested = Signal()
    product_search_requested = Signal(str)

    def __init__(
        self,
        sale_service=None,
        product_service=None,
        parent=None
    ):
        super().__init__(parent)

        self.sale_service = sale_service
        self.product_service = product_service

        self.cart_items = []
        self._product_results = []

        self._build_ui()
        self._apply_styles()

    # ==========================================
    # MAIN UI
    # ==========================================

    def _build_ui(self):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.setSpacing(18)

        # Product selection panel
        product_panel = self._build_product_panel()

        # Shopping cart panel
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

        # Product search
        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search by product name, SKU or barcode..."
        )

        self.search_input.setMinimumHeight(42)

        self.search_input.returnPressed.connect(
            self._search_products
        )

        self.product_cards_scroll = QScrollArea()
        self.product_cards_scroll.setObjectName("product_cards_scroll")
        self.product_cards_scroll.setWidgetResizable(True)
        self.product_cards_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.product_cards_container = QWidget()
        self.product_grid_layout = QGridLayout(
            self.product_cards_container
        )
        self.product_grid_layout.setContentsMargins(2, 2, 2, 2)
        self.product_grid_layout.setHorizontalSpacing(12)
        self.product_grid_layout.setVerticalSpacing(12)
        self.product_cards_container.setObjectName(
            "product_cards_container"
        )

        self.product_cards_scroll.setWidget(
            self.product_cards_container
        )

        layout.addWidget(heading)
        layout.addWidget(self.search_input)
        layout.addWidget(self.product_cards_scroll, 1)

        self._show_product_card_message(
            "Search for a product to see available items."
        )

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

        # Cart table
        self.cart_table = QTableWidget(0, 4)

        self.cart_table.setHorizontalHeaderLabels([
            "Item",
            "Qty",
            "Price",
            "Total",
        ])

        cart_header = self.cart_table.horizontalHeader()
        cart_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        cart_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        cart_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        cart_header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        self.cart_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.cart_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.cart_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setShowGrid(False)
        self.cart_table.setWordWrap(False)

        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.verticalHeader().setDefaultSectionSize(48)

        self.cart_table.itemSelectionChanged.connect(
            self._update_cart_action_buttons
        )

        # Cart action buttons
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

        # Sale summary
        summary = QFrame()

        summary_layout = QGridLayout(summary)

        self.subtotal_label = QLabel("0 MMK")
        self.discount_label = QLabel("0 MMK")
        self.tax_label = QLabel("0 MMK")

        self.total_label = QLabel("0 MMK")
        self.total_label.setObjectName("total_value")

        summary_layout.addWidget(
            QLabel("Subtotal"), 0, 0
        )

        summary_layout.addWidget(
            self.subtotal_label, 0, 1
        )

        summary_layout.addWidget(
            QLabel("Discount"), 1, 0
        )

        summary_layout.addWidget(
            self.discount_label, 1, 1
        )

        summary_layout.addWidget(
            QLabel("Tax"), 2, 0
        )

        summary_layout.addWidget(
            self.tax_label, 2, 1
        )

        summary_layout.addWidget(
            QLabel("Total"), 3, 0
        )

        summary_layout.addWidget(
            self.total_label, 3, 1
        )

        # Checkout button
        self.checkout_button = QPushButton(
            "Proceed to Checkout"
        )

        self.checkout_button.setObjectName("primary_button")
        self.checkout_button.setMinimumHeight(48)

        self.checkout_button.clicked.connect(
            self.checkout_requested.emit
        )

        # Add widgets
        layout.addWidget(heading)
        layout.addWidget(self.cart_table)
        layout.addLayout(action_layout)
        layout.addWidget(summary)
        layout.addWidget(self.checkout_button)

        self._update_cart_action_buttons()

        return panel

    # ==========================================
    # CART BUTTON STATES
    # ==========================================

    def _update_cart_action_buttons(self):

        has_selection = self.cart_table.currentRow() >= 0

        self.remove_button.setEnabled(has_selection)

        self.clear_button.setEnabled(
            bool(self.cart_items)
        )

    # ==========================================
    # PRODUCT SEARCH
    # ==========================================

    def _search_products(self):

        keyword = self.search_input.text().strip()

        if not keyword:
            self._product_results = []
            self._show_product_card_message(
                "Search for a product to see available items."
            )
            return

        if self.product_service is None:

            QMessageBox.warning(
                self,
                "Configuration Error",
                "Product service is not connected."
            )

            return

        try:

            products = self.product_service.search_pos_variants(
                keyword
            )
            self._product_results = products
            self._render_product_cards(products)

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Product Search Error",
                str(exc)
            )

    def _clear_product_cards(self):
        while self.product_grid_layout.count():
            layout_item = self.product_grid_layout.takeAt(0)
            widget = layout_item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_product_card_message(self, text):
        self._clear_product_cards()
        columns = self._available_product_columns()
        self._set_product_grid_columns(columns)
        message = QLabel(text)
        message.setObjectName("empty_products_label")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.product_grid_layout.addWidget(
            message, 0, 0, 1, columns
        )

    def _available_product_columns(self):
        margins = self.product_grid_layout.contentsMargins()
        spacing = self.product_grid_layout.horizontalSpacing()
        available_width = (
            self.product_cards_scroll.viewport().width()
            - margins.left()
            - margins.right()
        )
        columns = (available_width + spacing) // (180 + spacing)
        return max(1, min(3, columns))

    def _set_product_grid_columns(self, columns):
        for column in range(3):
            self.product_grid_layout.setColumnStretch(
                column,
                1 if column < columns else 0
            )

    @staticmethod
    def _variant_description(product):
        return " / ".join(
            value
            for value in (
                product.get("color_name"),
                product.get("size_name")
            )
            if value
        ) or "Default"

    def _create_product_card(self, product):
        card = QFrame()
        card.setObjectName("product_card")
        card.setMinimumWidth(180)
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        image_label = QLabel("No photo")
        image_label.setObjectName("product_photo")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setFixedHeight(132)

        image_path = self.product_service.resolve_product_image_path(
            product.get("image_path")
        )
        if image_path is not None and image_path.is_file():
            reader = QImageReader(str(image_path))
            if reader.canRead():
                image_size = reader.size()
                if image_size.isValid():
                    reader.setScaledSize(
                        image_size.scaled(
                            QSize(320, 132),
                            Qt.AspectRatioMode.KeepAspectRatio
                        )
                    )

                pixmap = QPixmap.fromImage(reader.read())
                if not pixmap.isNull():
                    image_label.setText("")
                    image_label.setPixmap(pixmap)

        name_label = QLabel(product["product_name"])
        name_label.setObjectName("product_name")
        name_label.setWordWrap(True)

        variant_label = QLabel(
            f'{product["sku"] or "No SKU"} | '
            f'{self._variant_description(product)}'
        )
        variant_label.setObjectName("product_details")
        variant_label.setWordWrap(True)

        price_stock_layout = QHBoxLayout()
        price_label = QLabel(
            f'{int(product["selling_price"]):,} MMK'
        )
        price_label.setObjectName("product_price")
        stock = int(product["quantity_on_hand"])
        stock_label = QLabel(
            "Out of stock" if stock <= 0 else f"{stock} in stock"
        )
        stock_label.setObjectName(
            "out_of_stock" if stock <= 0 else "stock_label"
        )
        price_stock_layout.addWidget(price_label)
        price_stock_layout.addStretch()
        price_stock_layout.addWidget(stock_label)

        add_button = QPushButton(
            "Out of stock" if stock <= 0 else "Add to Cart"
        )
        add_button.setObjectName("primary_button")
        add_button.setMinimumHeight(36)
        add_button.setEnabled(stock > 0)
        add_button.clicked.connect(
            lambda _checked=False, product_data=product:
                self._add_product_to_cart(product_data)
        )

        card_layout.addWidget(image_label)
        card_layout.addWidget(name_label)
        card_layout.addWidget(variant_label)
        card_layout.addLayout(price_stock_layout)
        card_layout.addWidget(add_button)
        return card

    def _render_product_cards(self, products):
        self._clear_product_cards()

        if not products:
            self._show_product_card_message(
                "No matching products found."
            )
            return

        columns = self._available_product_columns()
        self._set_product_grid_columns(columns)

        for index, product in enumerate(products):
            row, column = divmod(index, columns)
            self.product_grid_layout.addWidget(
                self._create_product_card(product),
                row,
                column,
                Qt.AlignmentFlag.AlignTop,
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._product_results:
            self._render_product_cards(self._product_results)

    # ==========================================
    # ADD PRODUCT TO CART
    # ==========================================

    def _add_product_to_cart(self, product):
        variant_id = product["variant_id"]
        product_name = product["product_name"]
        sku = product["sku"] or ""
        variant_name = self._variant_description(product)
        price = int(product["selling_price"])
        stock = int(product["quantity_on_hand"])

        if stock <= 0:

            QMessageBox.warning(
                self,
                "Out of stock",
                f"{product_name} ({sku}) is currently out of stock.\n"
                "Check inventory before adding it to this sale."
            )

            return

        # Check whether the variant already exists in cart
        existing_item = next(
            (
                item
                for item in self.cart_items
                if item["variant_id"] == variant_id
            ),
            None
        )

        if existing_item:

            if existing_item["quantity"] >= stock:

                QMessageBox.warning(
                    self,
                    "Stock limit reached",
                    f"Only {stock} unit(s) of {product_name} "
                    "are available."
                )

                return

            existing_item["quantity"] += 1

            existing_item["total"] = (
                existing_item["quantity"]
                * existing_item["price"]
            )

        else:

            self.cart_items.append({
                "variant_id": variant_id,
                "name": product_name,
                "sku": sku,
                "variant": variant_name,
                "price": price,
                "quantity": 1,
                "stock": stock,
                "image_path": product.get("image_path"),
                "total": price
            })

        self._refresh_cart()

    # ==========================================
    # INCREASE QUANTITY
    # ==========================================

    def _increase_selected_quantity(self):

        row = self.cart_table.currentRow()

        if row < 0 or row >= len(self.cart_items):
            return

        self._change_cart_quantity(
            self.cart_items[row]["variant_id"],
            1
        )

    def _decrease_selected_quantity(self):

        row = self.cart_table.currentRow()

        if row < 0 or row >= len(self.cart_items):
            return

        self._change_cart_quantity(
            self.cart_items[row]["variant_id"],
            -1
        )

    def _change_cart_quantity(self, variant_id, amount):

        item = next(
            (
                cart_item for cart_item in self.cart_items
                if cart_item["variant_id"] == variant_id
            ),
            None
        )

        if item is None:
            return

        if amount > 0 and item["quantity"] >= item["stock"]:
            QMessageBox.warning(
                self,
                "Stock limit reached",
                f"Only {item['stock']} unit(s) of "
                f"{item['name']} are available."
            )
            return

        if amount < 0 and item["quantity"] <= 1:
            return

        item["quantity"] += amount
        item["total"] = item["quantity"] * item["price"]

        self._refresh_cart()
        row = next(
            (
                index for index, cart_item in enumerate(self.cart_items)
                if cart_item["variant_id"] == variant_id
            ),
            -1
        )
        if row >= 0:
            self.cart_table.selectRow(row)

    # ==========================================
    # REMOVE CART ITEM
    # ==========================================

    def _remove_selected_item(self):

        row = self.cart_table.currentRow()

        if row < 0:
            return

        if row < len(self.cart_items):

            self.cart_items.pop(row)

        self._refresh_cart()

    # ==========================================
    # CLEAR CART
    # ==========================================

    def _clear_cart(self):

        self.cart_items.clear()

        self._refresh_cart()
        
        
    def reset_after_checkout(self):
        """Reset the cart after a successful checkout."""
        self.cart_items.clear()
        self._refresh_cart()

        keyword = self.search_input.text().strip()

        if keyword:
            self._search_products()
        else:
            self._product_results = []
            self._show_product_card_message(
                "Search for a product to see available items."
            )

    # ==========================================
    # REFRESH CART DISPLAY
    # ==========================================

    def _refresh_cart(self):

        self.cart_table.setRowCount(
            len(self.cart_items)
        )

        for row, item in enumerate(self.cart_items):

            display_name = (
                f'{item["name"]} '
                f'({item["sku"]}) - {item["variant"]}'
            )

            values = [
                display_name,
                f'{item["price"]:,}',
                f'{item["total"]:,}'
            ]

            self.cart_table.setItem(
                row,
                0,
                QTableWidgetItem(values[0])
            )

            quantity_widget = QWidget()
            quantity_layout = QHBoxLayout(quantity_widget)
            quantity_layout.setContentsMargins(2, 2, 2, 2)
            quantity_layout.setSpacing(4)

            decrease_button = QPushButton("-")
            decrease_button.setObjectName("quantity_button")
            decrease_button.setFixedSize(28, 28)
            decrease_button.setToolTip("Decrease quantity")
            decrease_button.setEnabled(item["quantity"] > 1)
            decrease_button.clicked.connect(
                lambda _checked=False, current_variant_id=item["variant_id"]:
                    self._change_cart_quantity(current_variant_id, -1)
            )

            quantity_label = QLabel(str(item["quantity"]))
            quantity_label.setObjectName("quantity_value")
            quantity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            quantity_label.setMinimumWidth(24)

            increase_button = QPushButton("+")
            increase_button.setObjectName("quantity_button")
            increase_button.setFixedSize(28, 28)
            increase_button.setToolTip("Increase quantity")
            increase_button.setEnabled(
                item["quantity"] < item["stock"]
            )
            increase_button.clicked.connect(
                lambda _checked=False, current_variant_id=item["variant_id"]:
                    self._change_cart_quantity(current_variant_id, 1)
            )

            quantity_layout.addWidget(decrease_button)
            quantity_layout.addWidget(quantity_label)
            quantity_layout.addWidget(increase_button)
            self.cart_table.setCellWidget(row, 1, quantity_widget)

            for column, value in enumerate(values[1:], start=2):
                self.cart_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value)
                )

        # Calculate subtotal
        subtotal = sum(
            item["total"]
            for item in self.cart_items
        )

        # Update summary
        self.subtotal_label.setText(
            f"{subtotal:,} MMK"
        )

        self.discount_label.setText("0 MMK")
        self.tax_label.setText("0 MMK")

        self.total_label.setText(
            f"{subtotal:,} MMK"
        )

        # Update button states
        self.checkout_button.setEnabled(
            bool(self.cart_items)
        )

        self._update_cart_action_buttons()

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
                color: #263B30;
            }

            QLineEdit:focus {
                border: 1px solid #315D40;
            }

            QScrollArea#product_cards_scroll {
                background-color: #F5F8F6;
                border: none;
            }

            QWidget#product_cards_container {
                background-color: #F5F8F6;
            }

            QFrame#product_card {
                background-color: #FFFFFF;
                border: 1px solid #DCE5DE;
                border-radius: 9px;
            }

            QLabel#product_photo {
                background-color: #F2F6F3;
                color: #718077;
                border: 1px solid #E1E8E3;
                border-radius: 6px;
            }

            QLabel#product_name {
                color: #203D2E;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#product_details {
                color: #718077;
                font-size: 11px;
            }

            QLabel#product_price {
                color: #203D2E;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#stock_label {
                color: #315D40;
                font-size: 11px;
            }

            QLabel#out_of_stock {
                color: #A94442;
                font-size: 11px;
                font-weight: bold;
            }

            QLabel#empty_products_label {
                color: #718077;
                padding: 32px;
            }

            QTableWidget {
                background-color: white;
                alternate-background-color: #F5F8F6;
                border: 1px solid #DCE5DE;
                border-radius: 8px;
                gridline-color: #EDF0ED;
                color: #263B30;
                selection-background-color: #DCECE1;
                selection-color: #203D2E;
                outline: none;
            }

            QTableWidget::item {
                padding: 7px;
                border-bottom: 1px solid #EDF0ED;
            }

            QTableWidget::item:selected {
                background-color: #DCECE1;
                color: #203D2E;
            }

            QHeaderView::section {
                background-color: #EAF1EC;
                color: #315D40;
                padding: 11px 8px;
                border: none;
                border-bottom: 1px solid #DCE5DE;
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

            #primary_button:disabled {
                background-color: #AABCAF;
                color: #F5F5F5;
            }

            #total_value {
                color: #203D2E;
                font-size: 20px;
                font-weight: bold;
            }

            QLabel#quantity_value {
                color: #203D2E;
                font-weight: bold;
            }

            QPushButton {
                background-color: #EAF1EC;
                color: #315D40;
                border: 1px solid #DCE5DE;
                padding: 8px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background-color: #DCECE1;
            }

            QPushButton#quantity_button {
                background-color: #EAF1EC;
                color: #315D40;
                border: 1px solid #B9CDBF;
                border-radius: 5px;
                padding: 0;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton#quantity_button:hover {
                background-color: #DCECE1;
            }

            QPushButton:disabled {
                background-color: #F2F4F2;
                color: #A0AAA2;
                border-color: #E5EAE6;
            }

            QMessageBox {
                background-color: #F5F7F5;
                color: #263B30;
            }

            QMessageBox QLabel {
                background-color: transparent;
                color: #263B30;
            }

            QMessageBox QPushButton {
                background-color: #EAF1EC;
                color: #203D2E;
                border: 1px solid #D0DDD4;
                border-radius: 6px;
                min-width: 72px;
                padding: 7px 12px;
            }

            QMessageBox QPushButton:hover {
                background-color: #DCE9DF;
            }

        """)
