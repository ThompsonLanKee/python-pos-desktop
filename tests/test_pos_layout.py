import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame

from src.views.main_window import MainWindow
from src.views.sale_view import SaleView


class PosLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_product_cards_use_three_columns_when_space_allows(self):
        product_service = Mock()
        product_service.resolve_product_image_path.return_value = None
        view = SaleView(product_service=product_service)
        view.resize(1400, 800)
        view.show()
        self.application.processEvents()

        products = [
            {
                "variant_id": index,
                "product_name": f"Product {index}",
                "sku": f"SKU-{index}",
                "color_name": "Blue",
                "size_name": "M",
                "selling_price": 1000,
                "quantity_on_hand": 4,
                "image_path": None,
            }
            for index in range(1, 5)
        ]
        view._product_results = products
        view._render_product_cards(products)
        self.application.processEvents()

        positions = [
            view.product_grid_layout.getItemPosition(index)[:2]
            for index in range(4)
        ]
        self.assertEqual(
            positions,
            [(0, 0), (0, 1), (0, 2), (1, 0)],
        )
        self.assertIn("#F5F8F6", view.styleSheet())

        view.resize(800, 800)
        self.application.processEvents()
        narrow_positions = [
            view.product_grid_layout.getItemPosition(index)[:2]
            for index in range(4)
        ]
        self.assertEqual(
            narrow_positions,
            [(0, 0), (0, 1), (1, 0), (1, 1)],
        )
        view.close()

    def test_sidebar_toggle_hides_and_restores_navigation(self):
        authorization_service = Mock()
        authorization_service.get_user_permissions.return_value = [
            "SALE_CREATE"
        ]
        product_service = Mock()
        product_service.resolve_product_image_path.return_value = None

        window = MainWindow(
            SimpleNamespace(
                user_id=1,
                full_name="Test User",
                username="tester",
            ),
            None,
            authorization_service,
            None,
            None,
            None,
            product_service,
            None,
        )

        window.sidebar_toggle_button.click()
        self.assertTrue(window.sidebar.isHidden())
        self.assertEqual(
            window.sidebar_toggle_button.toolTip(),
            "Show navigation",
        )

        window.sidebar_toggle_button.click()
        self.assertFalse(window.sidebar.isHidden())
        self.assertEqual(
            window.sidebar_toggle_button.toolTip(),
            "Hide navigation",
        )
        window.close()

    def test_single_product_card_keeps_its_content_height(self):
        product_service = Mock()
        product_service.resolve_product_image_path.return_value = None
        view = SaleView(product_service=product_service)
        view.resize(1400, 800)
        view.show()
        self.application.processEvents()

        product = {
            "variant_id": 1,
            "product_name": "Laptop",
            "sku": "LAPTOP-1",
            "color_name": None,
            "size_name": None,
            "selling_price": 2500000,
            "quantity_on_hand": 1,
            "image_path": None,
        }
        view._product_results = [product]
        view._render_product_cards([product])
        self.application.processEvents()

        card = view.product_cards_container.findChild(
            QFrame,
            "product_card",
        )
        self.assertIsNotNone(card)
        self.assertLess(card.y(), 20)
        self.assertLess(
            card.height(),
            view.product_cards_scroll.viewport().height() // 2,
        )
        view.close()


if __name__ == "__main__":
    unittest.main()
