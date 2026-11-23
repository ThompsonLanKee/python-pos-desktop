from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QTabWidget,
)
from src.views.category_tab import CategoryTab


class ProductPhotosTab(QWidget):
    """Manage product photos used by the point-of-sale catalog."""

    def __init__(self, product_service, parent=None):
        super().__init__(parent)

        self.product_service = product_service
        self.products = []

        self.setStyleSheet("""
            QLineEdit, QTableWidget {
                background-color: #FFFFFF;
                color: #26352C;
                border: 1px solid #DCE5DE;
                border-radius: 7px;
            }
            QLineEdit {
                padding: 9px 10px;
            }
            QTableWidget {
                alternate-background-color: #F5F8F6;
                gridline-color: #E5EAE6;
                selection-background-color: #D6EBDD;
                selection-color: #203D2E;
            }
            QHeaderView::section {
                background-color: #EAF1EC;
                color: #203D2E;
                padding: 10px;
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
            QLabel#page_subtitle {
                color: #718077;
            }
            QLabel#photo_thumbnail {
                background-color: #F2F6F3;
                color: #718077;
                border: 1px solid #E1E8E3;
                border-radius: 5px;
            }
        """)

        self._build_ui()
        self.load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        heading = QLabel("Product Photos")
        heading.setObjectName("section_title")
        subtitle = QLabel(
            "Add photos used on product cards at the point of sale."
        )
        subtitle.setObjectName("page_subtitle")

        layout.addWidget(heading)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search products by name or brand..."
        )
        self.search_input.textChanged.connect(self.load_products)
        toolbar.addWidget(self.search_input, 1)

        self.upload_button = QPushButton("Add Photo")
        self.upload_button.setObjectName("primary_button")
        self.upload_button.clicked.connect(self.choose_product_photo)
        toolbar.addWidget(self.upload_button)

        self.remove_button = QPushButton("Remove Photo")
        self.remove_button.clicked.connect(self.remove_product_photo)
        toolbar.addWidget(self.remove_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(
            lambda: self.load_products()
        )
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        self.product_table = QTableWidget(0, 3)
        self.product_table.setHorizontalHeaderLabels([
            "Product",
            "Brand",
            "Photo",
        ])
        self.product_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.product_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.product_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.product_table.setAlternatingRowColors(True)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.verticalHeader().setDefaultSectionSize(82)
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.product_table.setColumnWidth(2, 112)
        self.product_table.itemSelectionChanged.connect(
            self._update_action_buttons
        )
        layout.addWidget(self.product_table, 1)

        self.result_label = QLabel("0 products")
        self.result_label.setObjectName("page_subtitle")
        layout.addWidget(self.result_label)

        self._update_action_buttons()

    def load_products(
        self,
        search_text: str | None = None,
        selected_product_id=None
    ):
        try:
            if selected_product_id is None:
                selected_product_id = self._selected_product_id()

            self.products = self.product_service.search_products(
                search_text
                if search_text is not None
                else self.search_input.text()
            )

            self.product_table.setRowCount(len(self.products))
            selected_row = -1

            for row, product in enumerate(self.products):
                name_item = QTableWidgetItem(product.product_name)
                name_item.setData(
                    Qt.ItemDataRole.UserRole,
                    product.product_id
                )
                self.product_table.setItem(row, 0, name_item)
                self.product_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(product.brand or "")
                )
                self.product_table.setCellWidget(
                    row,
                    2,
                    self._create_thumbnail(product.image_path)
                )

                if product.product_id == selected_product_id:
                    selected_row = row

            if selected_row < 0 and self.products:
                selected_row = 0
            if selected_row >= 0:
                self.product_table.selectRow(selected_row)

            self.result_label.setText(
                f"{len(self.products)} product(s) found"
            )
            self._update_action_buttons()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Product Load Error",
                f"Could not load products:\n{exc}"
            )

    def _create_thumbnail(self, image_path):
        label = QLabel("No photo")
        label.setObjectName("photo_thumbnail")
        label.setFixedSize(92, 64)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        path = self.product_service.resolve_product_image_path(
            image_path
        )
        if path is None or not path.is_file():
            return label

        reader = QImageReader(str(path))
        if not reader.canRead():
            return label

        image_size = reader.size()
        if image_size.isValid():
            reader.setScaledSize(
                image_size.scaled(
                    QSize(88, 60),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
            )

        pixmap = QPixmap.fromImage(reader.read())
        if pixmap.isNull():
            return label

        label.setText("")
        label.setPixmap(pixmap)
        return label

    def _selected_product(self):
        row = self.product_table.currentRow()
        if row < 0:
            return None

        name_item = self.product_table.item(row, 0)
        if name_item is None:
            return None

        product_id = name_item.data(Qt.ItemDataRole.UserRole)
        return next(
            (
                product for product in self.products
                if product.product_id == product_id
            ),
            None
        )

    def _selected_product_id(self):
        product = self._selected_product()
        return product.product_id if product else None

    def _update_action_buttons(self):
        product = self._selected_product()
        self.upload_button.setEnabled(product is not None)
        self.remove_button.setEnabled(
            product is not None and bool(product.image_path)
        )
        self.upload_button.setText(
            "Change Photo"
            if product is not None and product.image_path
            else "Add Photo"
        )

    def choose_product_photo(self):
        product = self._selected_product()
        if product is None:
            return

        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Product Photo",
            "",
            "Image files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not image_path:
            return

        reader = QImageReader(image_path)
        if not reader.canRead():
            QMessageBox.warning(
                self,
                "Invalid Image",
                "The selected file could not be opened as an image."
            )
            return

        try:
            self.product_service.set_product_image(
                product.product_id,
                image_path
            )
            self.load_products(selected_product_id=product.product_id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Photo Upload Error",
                f"Could not save the product photo:\n{exc}"
            )

    def remove_product_photo(self):
        product = self._selected_product()
        if product is None or not product.image_path:
            return

        confirmation = QMessageBox.question(
            self,
            "Remove Product Photo",
            f"Remove the photo for {product.product_name}?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            self.product_service.remove_product_image(
                product.product_id
            )
            self.load_products(selected_product_id=product.product_id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Photo Removal Error",
                f"Could not remove the product photo:\n{exc}"
            )
            
class ProductManagementView(QWidget):
    """Combined product management screen."""

    def __init__(self, product_service, parent=None):
        super().__init__(parent)

        self.product_service = product_service
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F8F6;
                color: #203D2E;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget {
                background-color: #F5F8F6;
                color: #203D2E;
            }

            QTabWidget::pane {
                background-color: #F5F8F6;
                border: 1px solid #DCE5DE;
                border-top: none;
            }

            QTabBar {
                background-color: #F5F8F6;
            }

            QTabBar::tab {
                background-color: #E8EFEA;
                color: #203D2E;
                padding: 11px 24px;
                margin-right: 3px;
                border: 1px solid #D5E1D8;
                border-bottom: none;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                font-weight: 600;
            }

            QTabBar::tab:selected {
                background-color: #315D40;
                color: #FFFFFF;
                border-color: #315D40;
            }

            QTabBar::tab:hover:!selected {
                background-color: #D6EBDD;
                color: #203D2E;
            }
        """)

        # Categories tab
        self.category_tab = CategoryTab(
            database=product_service.database
        )
        self.tabs.addTab(
            self.category_tab,
            "Categories"
        )

        # Products tab - implemented in the next stage
        self.products_placeholder = QWidget()
        products_layout = QVBoxLayout(
            self.products_placeholder
        )

        products_message = QLabel(
            "Product management will be implemented next."
        )
        products_message.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        products_message.setStyleSheet(
            "color: #718077; font-size: 15px;"
        )

        products_layout.addWidget(products_message)

        self.tabs.addTab(
            self.products_placeholder,
            "Products"
        )

        # Existing product photo functionality
        self.photos_tab = ProductPhotosTab(
            product_service=product_service
        )
        self.tabs.addTab(
            self.photos_tab,
            "Photos"
        )

        layout.addWidget(self.tabs)