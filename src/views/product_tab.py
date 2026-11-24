from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QDialog,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDoubleSpinBox, QGroupBox
)
from src.models import Product, ProductVariant


FORM_STYLE = """
QDialog { background-color: #F5F8F6; color: #203D2E; }
QLabel { color: #203D2E; background: transparent; font-size: 13px; }
QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox {
    background: #FFFFFF; color: #203D2E;
    border: 1px solid #C8D8CD; border-radius: 7px; padding: 8px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #43845A;
}
QPushButton {
    background: #E6EEE8; color: #203D2E;
    border: 1px solid #C8D8CD; border-radius: 7px;
    padding: 9px 16px; min-width: 70px;
}
QPushButton#primary_button {
    background: #315D40; color: #FFFFFF; border: none; font-weight: 600;
}
QPushButton#primary_button:hover { background: #43845A; }
QComboBox QAbstractItemView {
    background: #FFFFFF; color: #203D2E;
    selection-background-color: #D6EBDD; selection-color: #203D2E;
}
"""


class ProductDialog(QDialog):
    def __init__(self, categories, product_data=None, parent=None):
        super().__init__(parent)
        self.categories = categories
        self.product_data = product_data
        self.setWindowTitle("Edit Product" if product_data else "Add Product")
        self.setMinimumWidth(540)
        self.setStyleSheet(FORM_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)
        self.name_input = QLineEdit()
        self.name_input.setMaxLength(150)
        self.name_input.setPlaceholderText("Enter product name")
        self.brand_input = QLineEdit()
        self.brand_input.setMaxLength(100)
        self.brand_input.setPlaceholderText("Optional brand")
        self.category_combo = QComboBox()
        self.category_combo.addItem("Select a category", None)
        for category in self.categories:
            if category["is_active"]:
                self.category_combo.addItem(
                    category["category_name"], category["category_id"]
                )
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional product description")
        self.description_input.setFixedHeight(75)
        form.addRow("Product Name *", self.name_input)
        form.addRow("Brand", self.brand_input)
        form.addRow("Category *", self.category_combo)
        form.addRow("Description", self.description_input)
        layout.addLayout(form)

        self.variant_group = QGroupBox("Initial Variant")
        vf = QFormLayout(self.variant_group)
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Required unique SKU")
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Optional barcode")
        self.cost_input = self._price_input()
        self.selling_input = self._price_input()
        vf.addRow("SKU *", self.sku_input)
        vf.addRow("Barcode", self.barcode_input)
        vf.addRow("Cost Price", self.cost_input)
        vf.addRow("Selling Price", self.selling_input)
        layout.addWidget(self.variant_group)

        if self.product_data:
            self.variant_group.hide()
            self.name_input.setText(self.product_data["product_name"])
            self.brand_input.setText(self.product_data.get("brand") or "")
            self.description_input.setPlainText(self.product_data.get("description") or "")
            index = self.category_combo.findData(self.product_data["category_id"])
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setObjectName("primary_button")
        save.clicked.connect(self._validate)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    @staticmethod
    def _price_input():
        widget = QDoubleSpinBox()
        widget.setRange(0, 999999999)
        widget.setDecimals(2)
        widget.setPrefix("MMK ")
        return widget

    def _validate(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        if self.category_combo.currentData() is None:
            QMessageBox.warning(self, "Validation", "Please select a category.")
            return
        if not self.product_data and not self.sku_input.text().strip():
            QMessageBox.warning(self, "Validation", "SKU is required.")
            return
        self.accept()

    def get_product_data(self):
        return {
            "product_name": self.name_input.text().strip(),
            "brand": self.brand_input.text().strip() or None,
            "category_id": self.category_combo.currentData(),
            "description": self.description_input.toPlainText().strip() or None,
        }

    def get_variant_data(self):
        return {
            "sku": self.sku_input.text().strip().upper(),
            "barcode": self.barcode_input.text().strip() or None,
            "color_id": None, "size_id": None,
            "cost_price": self.cost_input.value(),
            "selling_price": self.selling_input.value(),
            "is_active": True,
        }


class VariantDialog(QDialog):
    def __init__(self, options, variant=None, parent=None):
        super().__init__(parent)
        self.variant = variant
        self.setWindowTitle("Edit Variant" if variant else "Add Variant")
        self.setMinimumWidth(500)
        self.setStyleSheet(FORM_STYLE)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Unique SKU")
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Optional barcode")

        self.color_combo = QComboBox()
        self.color_combo.addItem("No Color", None)
        for color in options["colors"]:
            self.color_combo.addItem(color["color_name"], color["color_id"])

        self.size_combo = QComboBox()
        self.size_combo.addItem("No Size", None)
        for size in options["sizes"]:
            self.size_combo.addItem(size["size_name"], size["size_id"])

        self.cost_input = ProductDialog._price_input()
        self.selling_input = ProductDialog._price_input()

        form.addRow("SKU *", self.sku_input)
        form.addRow("Barcode", self.barcode_input)
        form.addRow("Color", self.color_combo)
        form.addRow("Size", self.size_combo)
        form.addRow("Cost Price", self.cost_input)
        form.addRow("Selling Price", self.selling_input)
        layout.addLayout(form)

        if variant:
            self.sku_input.setText(variant.get("sku") or "")
            self.barcode_input.setText(variant.get("barcode") or "")
            self.color_combo.setCurrentIndex(max(0, self.color_combo.findData(variant.get("color_id"))))
            self.size_combo.setCurrentIndex(max(0, self.size_combo.findData(variant.get("size_id"))))
            self.cost_input.setValue(float(variant.get("cost_price") or 0))
            self.selling_input.setValue(float(variant.get("selling_price") or 0))

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setObjectName("primary_button")
        save.clicked.connect(self._validate)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _validate(self):
        if not self.sku_input.text().strip():
            QMessageBox.warning(self, "Validation", "SKU is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "sku": self.sku_input.text().strip().upper(),
            "barcode": self.barcode_input.text().strip() or None,
            "color_id": self.color_combo.currentData(),
            "size_id": self.size_combo.currentData(),
            "cost_price": self.cost_input.value(),
            "selling_price": self.selling_input.value(),
        }


class VariantManagementDialog(QDialog):
    def __init__(self, product_service, product_id, product_name, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.product_id = product_id
        self.setWindowTitle(f"Variants — {product_name}")
        self.resize(1000, 520)
        self.setStyleSheet(FORM_STYLE + """
            QTableWidget {
                background: white; color: #26352C;
                gridline-color: #E5EAE6;
                selection-background-color: #C7E4D0;
                selection-color: #203D2E;
            }
            QHeaderView::section {
                background: #EAF1EC; color: #203D2E;
                padding: 9px; border: none; font-weight: 600;
            }
        """)
        layout = QVBoxLayout(self)
        heading = QLabel(f"Manage variants for: {product_name}")
        heading.setStyleSheet("font-size: 17px; font-weight: 700;")
        layout.addWidget(heading)

        toolbar = QHBoxLayout()
        self.add_button = QPushButton("Add Variant")
        self.add_button.setObjectName("primary_button")
        self.add_button.clicked.connect(self.add_variant)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_variant)
        self.status_button = QPushButton("Deactivate")
        self.status_button.clicked.connect(self.toggle_status)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.load_variants)
        for b in (self.add_button, self.edit_button, self.status_button, refresh):
            toolbar.addWidget(b)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "SKU", "Barcode", "Color", "Size", "Cost Price",
            "Selling Price", "Stock", "Status"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda *_: self.edit_variant())
        layout.addWidget(self.table)
        self.load_variants()

    def load_variants(self):
        details = self.product_service.get_product_details(self.product_id)
        self.variants = details["variants"] if details else []
        self.table.setRowCount(len(self.variants))
        for row, v in enumerate(self.variants):
            values = [
                v.get("sku") or "", v.get("barcode") or "",
                v.get("color_name") or "—", v.get("size_name") or "—",
                f'{float(v.get("cost_price") or 0):,.2f}',
                f'{float(v.get("selling_price") or 0):,.2f}',
                str(v.get("quantity_on_hand") or 0),
                "Active" if v.get("is_active") else "Inactive",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, v["variant_id"])
                self.table.setItem(row, col, item)
        self._update_buttons()

    def _selected_variant(self):
        row = self.table.currentRow()
        if row < 0 or self.table.item(row, 0) is None:
            return None
        variant_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((v for v in self.variants if v["variant_id"] == variant_id), None)

    def _update_buttons(self):
        v = self._selected_variant()
        self.edit_button.setEnabled(v is not None)
        self.status_button.setEnabled(v is not None)
        self.status_button.setText("Deactivate" if v and v["is_active"] else "Activate")

    def add_variant(self):
        options = self.product_service.get_variant_options()
        dialog = VariantDialog(options, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.product_service.create_variant(self.product_id, dialog.get_data())
            self.load_variants()
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Add Variant", str(exc))

    def edit_variant(self):
        variant = self._selected_variant()
        if not variant:
            return
        options = self.product_service.get_variant_options()
        dialog = VariantDialog(options, variant=variant, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.product_service.update_variant(
                variant["variant_id"], dialog.get_data()
            )
            self.load_variants()
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Update Variant", str(exc))

    def toggle_status(self):
        variant = self._selected_variant()
        if not variant:
            return
        new_status = not bool(variant["is_active"])
        action = "activate" if new_status else "deactivate"
        answer = QMessageBox.question(
            self, "Confirm",
            f"Are you sure you want to {action} variant '{variant['sku']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.product_service.set_variant_active(
                variant["variant_id"], new_status
            )
            self.load_variants()
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Change Status", str(exc))


class ProductsTab(QWidget):
    def __init__(self, product_service, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.products = []
        self.categories = []
        self.setStyleSheet("""
            QLineEdit, QComboBox, QTableWidget {
                background: #FFFFFF; color: #26352C;
                border: 1px solid #DCE5DE; border-radius: 7px;
            }
            QLineEdit, QComboBox { padding: 8px; }
            QTableWidget {
                alternate-background-color: #F5F8F6;
                gridline-color: #E5EAE6;
                selection-background-color: #C7E4D0;
                selection-color: #203D2E;
            }
            QTableWidget::item:selected { background: #C7E4D0; color: #203D2E; }
            QHeaderView::section {
                background: #EAF1EC; color: #203D2E;
                padding: 10px; border: none; font-weight: 600;
            }
            QPushButton {
                background: #EAF1EC; color: #203D2E;
                border: 1px solid #D0DDD4; border-radius: 6px;
                padding: 8px 13px;
            }
            QPushButton:hover { background: #DCE9DF; }
            QPushButton#primary_button { background: #315D40; color: white; border: none; }
            QPushButton#primary_button:hover { background: #3F7653; }
            QPushButton:disabled { color: #8A968E; background: #EEF1EF; }
        """)
        self._build_ui()
        self.load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        title = QLabel("Products")
        title.setStyleSheet("color: #203D2E; font-size: 19px; font-weight: 700;")
        subtitle = QLabel("Manage product information, categories, variants and selling prices.")
        subtitle.setStyleSheet("color: #718077;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by product name or brand...")
        self.search_input.textChanged.connect(self.load_products)
        toolbar.addWidget(self.search_input, 1)
        self.category_filter = QComboBox()
        self.category_filter.currentIndexChanged.connect(self.load_products)
        self.category_filter.setMinimumWidth(180)
        toolbar.addWidget(self.category_filter)

        self.add_button = QPushButton("Add Product")
        self.add_button.setObjectName("primary_button")
        self.add_button.clicked.connect(self.add_product)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_product)
        self.variants_button = QPushButton("Manage Variants")
        self.variants_button.clicked.connect(self.manage_variants)
        self.status_button = QPushButton("Deactivate")
        self.status_button.clicked.connect(self.toggle_product_status)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.load_products)
        for b in (self.add_button, self.edit_button, self.variants_button, self.status_button, refresh):
            toolbar.addWidget(b)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Product", "Brand", "Category", "Variants", "Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda *_: self.edit_product())
        layout.addWidget(self.table, 1)
        self.result_label = QLabel("0 products")
        self.result_label.setStyleSheet("color: #718077;")
        layout.addWidget(self.result_label)
        self._update_buttons()

    def _load_categories(self):
        with self.product_service.database.connect() as connection:
            rows = connection.execute("""
                SELECT category_id, category_name, is_active
                FROM categories ORDER BY category_name COLLATE NOCASE
            """).fetchall()
        self.categories = [dict(row) for row in rows]
        current_id = self.category_filter.currentData()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        for c in self.categories:
            if c["is_active"]:
                self.category_filter.addItem(c["category_name"], c["category_id"])
        index = self.category_filter.findData(current_id)
        self.category_filter.setCurrentIndex(max(index, 0))
        self.category_filter.blockSignals(False)

    def load_products(self, *_):
        try:
            selected_id = self._selected_product_id()
            self._load_categories()
            self.products = self.product_service.search_products(self.search_input.text())
            category_id = self.category_filter.currentData()
            if category_id is not None:
                self.products = [p for p in self.products if p.category_id == category_id]
            category_names = {c["category_id"]: c["category_name"] for c in self.categories}
            self.table.setRowCount(len(self.products))
            selected_row = -1
            for row, product in enumerate(self.products):
                details = self.product_service.get_product_details(product.product_id)
                variants = details["variants"] if details else []
                values = [
                    product.product_name, product.brand or "",
                    category_names.get(product.category_id, "—"),
                    str(len(variants)), "Active" if product.is_active else "Inactive",
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, product.product_id)
                    self.table.setItem(row, col, item)
                if product.product_id == selected_id:
                    selected_row = row
            if selected_row >= 0:
                self.table.selectRow(selected_row)
            self.result_label.setText(f"{len(self.products)} product(s) found")
            self._update_buttons()
        except Exception as exc:
            QMessageBox.critical(self, "Product Load Error", f"Could not load products:\n{exc}")

    def _selected_product(self):
        row = self.table.currentRow()
        if row < 0 or self.table.item(row, 0) is None:
            return None
        product_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((p for p in self.products if p.product_id == product_id), None)

    def _selected_product_id(self):
        product = self._selected_product()
        return product.product_id if product else None

    def _update_buttons(self):
        product = self._selected_product()
        self.edit_button.setEnabled(product is not None)
        self.variants_button.setEnabled(product is not None)
        self.status_button.setEnabled(product is not None)
        self.status_button.setText("Deactivate" if product and product.is_active else "Activate")

    def add_product(self):
        self._load_categories()
        active = [c for c in self.categories if c["is_active"]]
        if not active:
            QMessageBox.warning(self, "No Categories", "Create an active category before adding a product.")
            return
        dialog = ProductDialog(active, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            data = dialog.get_product_data()
            product = Product(
                product_name=data["product_name"], category_id=data["category_id"],
                description=data["description"], brand=data["brand"],
            )
            self.product_service.create_product(product, [dialog.get_variant_data()])
            self.load_products()
            QMessageBox.information(self, "Product Created", "Product and initial variant created.")
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Create Product", str(exc))

    def edit_product(self):
        selected = self._selected_product()
        if not selected:
            return
        details = self.product_service.get_product_details(selected.product_id)
        if not details:
            QMessageBox.warning(self, "Product Not Found", "This product no longer exists.")
            self.load_products()
            return
        dialog = ProductDialog(self.categories, product_data=details["product"], parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            data = dialog.get_product_data()
            product = Product(
                product_id=selected.product_id, product_name=data["product_name"],
                category_id=data["category_id"], description=data["description"],
                brand=data["brand"], is_active=selected.is_active,
            )
            self.product_service.update_product(product)
            self.load_products()
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Update Product", str(exc))

    def manage_variants(self):
        product = self._selected_product()
        if not product:
            return
        dialog = VariantManagementDialog(
            self.product_service, product.product_id, product.product_name, self
        )
        dialog.exec()
        self.load_products()

    def toggle_product_status(self):
        product = self._selected_product()
        if not product:
            return
        new_status = not bool(product.is_active)
        action = "activate" if new_status else "deactivate"
        answer = QMessageBox.question(
            self, "Confirm Product Status",
            f"Are you sure you want to {action} '{product.product_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.product_service.set_product_active(product.product_id, new_status)
            self.load_products()
        except Exception as exc:
            QMessageBox.warning(self, "Unable to Change Product Status", str(exc))
