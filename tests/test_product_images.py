import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

import src.core.database as database_module
import src.services.product_service as product_service_module
from src.core.database import Database
from src.models import Category, Product
from src.repositories import CategoryRepository
from src.services.product_service import ProductService
from src.views.product_view import ProductManagementView
from src.views.sale_view import SaleView


class ProductImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="pos-product-images-"
        )
        self.old_data_dir = database_module.DATA_DIR
        self.old_database_path = database_module.DATABASE_PATH
        self.old_service_data_dir = product_service_module.DATA_DIR

        self.data_dir = Path(self.temporary_directory.name) / "data"
        self.data_dir.mkdir()
        database_module.DATA_DIR = self.data_dir
        database_module.DATABASE_PATH = self.data_dir / "pos.db"
        product_service_module.DATA_DIR = self.data_dir

        with closing(sqlite3.connect(database_module.DATABASE_PATH)) as conn:
            conn.execute("""
                CREATE TABLE products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    description TEXT,
                    category_id INTEGER NOT NULL,
                    brand TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

        self.database = Database()
        self.database.initialize()

        category_id = CategoryRepository(self.database).create(
            Category(category_name="Photo Test Category")
        )
        self.product_service = ProductService(self.database)
        self.product_id = self.product_service.create_product(
            Product(
                product_name="Photo Test Product",
                category_id=category_id
            ),
            [{
                "sku": "PHOTO-TEST-SKU",
                "color_id": None,
                "size_id": None,
                "cost_price": 100,
                "selling_price": 250
            }]
        )

        self.sale_view = None
        self.management_view = None

    def tearDown(self):
        for view in (self.sale_view, self.management_view):
            if view is not None:
                view.close()
                view.deleteLater()
        QCoreApplication.sendPostedEvents(
            None,
            QEvent.Type.DeferredDelete
        )
        self.application.processEvents()
        self.sale_view = None
        self.management_view = None
        database_module.DATA_DIR = self.old_data_dir
        database_module.DATABASE_PATH = self.old_database_path
        product_service_module.DATA_DIR = self.old_service_data_dir
        self.temporary_directory.cleanup()

    @staticmethod
    def _create_image(path, color):
        image = QImage(32, 32, QImage.Format.Format_RGB32)
        image.fill(QColor(color))
        if not image.save(str(path)):
            raise AssertionError(f"Could not create image fixture: {path}")

    def test_product_photo_is_migrated_managed_and_shown_in_pos(self):
        with closing(self.database.connect()) as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(products)")
            }
        self.assertIn("image_path", columns)

        first_source = Path(self.temporary_directory.name) / "first.png"
        second_source = Path(self.temporary_directory.name) / "second.png"
        self._create_image(first_source, "#3F7653")
        self._create_image(second_source, "#315D40")

        first_path = self.product_service.set_product_image(
            self.product_id,
            first_source
        )
        first_image = self.product_service.resolve_product_image_path(
            first_path
        )
        self.assertIsNotNone(first_image)
        self.assertTrue(first_image.is_file())
        self.assertEqual(
            self.product_service.search_pos_variants(
                "Photo Test Product"
            )[0]["image_path"],
            first_path
        )

        self.management_view = ProductManagementView(
            self.product_service
        )
        self.assertEqual(self.management_view.product_table.rowCount(), 1)
        thumbnail = self.management_view.product_table.cellWidget(0, 2)
        self.assertIsInstance(thumbnail, QLabel)
        self.assertFalse(thumbnail.pixmap().isNull())
        self.management_view.search_input.setText("no matching product")
        self.assertEqual(self.management_view.product_table.rowCount(), 0)
        self.management_view.search_input.clear()
        self.assertEqual(self.management_view.product_table.rowCount(), 1)

        variant = self.product_service.search_pos_variants(
            "Photo Test Product"
        )[0]
        with self.database.transaction() as conn:
            conn.execute(
                """
                UPDATE inventory
                SET quantity_on_hand = 2
                WHERE variant_id = ?
                """,
                (variant["variant_id"],)
            )

        self.sale_view = SaleView(product_service=self.product_service)
        self.sale_view.search_input.setText("Photo Test Product")
        self.sale_view._search_products()
        card_photo = self.sale_view.product_cards_container.findChild(
            QLabel,
            "product_photo"
        )
        self.assertIsNotNone(card_photo)
        self.assertFalse(card_photo.pixmap().isNull())

        add_button = next(
            button
            for button in self.sale_view.product_cards_container.findChildren(
                QPushButton
            )
            if button.text() == "Add to Cart"
        )
        add_button.click()
        self.assertEqual(self.sale_view.cart_items[0]["quantity"], 1)

        quantity_buttons = self.sale_view.cart_table.cellWidget(
            0, 1
        ).findChildren(QPushButton)
        quantity_buttons[1].click()
        self.assertEqual(self.sale_view.cart_items[0]["quantity"], 2)

        second_path = self.product_service.set_product_image(
            self.product_id,
            second_source
        )
        second_image = self.product_service.resolve_product_image_path(
            second_path
        )
        self.assertFalse(first_image.exists())
        self.assertTrue(second_image.is_file())

        self.assertTrue(
            self.product_service.remove_product_image(self.product_id)
        )
        self.assertFalse(second_image.exists())
        details = self.product_service.get_product_details(self.product_id)
        self.assertIsNone(details["product"]["image_path"])


if __name__ == "__main__":
    unittest.main()
