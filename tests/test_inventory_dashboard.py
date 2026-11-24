import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QApplication, QDialog, QMessageBox, QPushButton
)

from src.views import inventory_view
from src.views.inventory_view import InventoryView


class InventoryDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.today = QDate.currentDate().toString("yyyy-MM-dd")
        previous_day = QDate.currentDate().addDays(-1).toString("yyyy-MM-dd")
        self.items = [
            self._item(1, "LOW-1", "Low Product", 2, 3),
            self._item(2, "OUT-1", "Out Product", 0, 0),
            self._item(3, "IN-1", "In Product", 8, 3),
            self._item(4, "INACTIVE-1", "Inactive Product", 100, 2, 0),
        ]
        self.transactions = [
            {"created_at": f"{self.today} 10:00:00", "quantity_change": 4},
            {"created_at": f"{self.today} 11:00:00", "quantity_change": -2},
            {"created_at": f"{previous_day} 10:00:00", "quantity_change": 90},
        ]
        self.service = _InventoryService(self.items, self.transactions)
        self.view = InventoryView(self.service)

    def tearDown(self):
        self.view.close()

    @staticmethod
    def _item(variant_id, sku, name, quantity, reorder, active=1):
        return {
            "variant_id": variant_id,
            "sku": sku,
            "product_name": name,
            "quantity_on_hand": quantity,
            "reorder_level": reorder,
            "is_active": active,
            "barcode": None,
            "color_name": None,
            "size_name": None,
            "cost_price": 5,
            "selling_price": 10,
            "category_name": "Test",
        }

    def test_dashboard_uses_active_inventory_and_transaction_data(self):
        self.view.resize(900, 650)
        self.view.show()
        self.application.processEvents()
        self.assertLessEqual(
            self.view.dashboard_scroll.widget().width(),
            self.view.dashboard_scroll.viewport().width() + 1,
        )

        self.assertEqual(
            [
                self.view.tabs.tabText(index)
                for index in range(self.view.tabs.count())
            ],
            [
                "Dashboard",
                "Stock Overview",
                "Movement History",
                "Inventory Reports",
            ],
        )
        self.assertEqual(self.view.dashboard_total_items.text(), "3")
        self.assertEqual(self.view.dashboard_total_units.text(), "10")
        self.assertEqual(self.view.dashboard_low_stock.text(), "1")
        self.assertEqual(self.view.dashboard_out_of_stock.text(), "1")

        self.view.dashboard_start_date.setDate(QDate.currentDate())
        self.view.dashboard_end_date.setDate(QDate.currentDate())
        movement_series = self.view.movement_chart.series()[0]
        stock_in, stock_out = movement_series.barSets()
        self.assertEqual(stock_in.at(0), 4)
        self.assertEqual(stock_out.at(0), 2)
        self.assertIn("Net Movement: +2", self.view.movement_totals_label.text())

        low_stock_button = next(
            button for button in self.view.findChildren(QPushButton)
            if button.text() == "Low Stock"
        )
        low_stock_button.click()
        self.assertEqual(self.view.tabs.currentIndex(), 1)
        self.assertEqual(self.view.stock_table.rowCount(), 1)

    def test_rejected_issue_shows_available_stock_warning(self):
        class AcceptedMovementDialog:
            created = []

            def __init__(self, item, title, parent=None):
                self.created.append((item, title, parent))

            def exec(self):
                return QDialog.DialogCode.Accepted

            def get_data(self):
                return {"quantity": 5, "notes": None}

        messages = []
        self.view._show_message = (
            lambda icon, title, text: messages.append((icon, title, text))
        )
        with patch.object(
            inventory_view, "StockMovementDialog", AcceptedMovementDialog
        ):
            self.view.perform_movement("issue", self.items[0])

        self.assertEqual(AcceptedMovementDialog.created[0][0], self.items[0])
        self.assertEqual(self.service.last_issue, (1, 5, None))
        self.assertEqual(messages[-1][0], QMessageBox.Icon.Warning)
        self.assertEqual(messages[-1][1], "Stock Movement Rejected")
        self.assertIn("Only 2 unit(s) are currently available", messages[-1][2])

    def test_dashboard_handles_empty_inventory_and_history(self):
        self.service.items = []
        self.service.transactions = []
        self.view.load_dashboard()

        self.assertEqual(self.view.dashboard_total_items.text(), "0")
        self.assertEqual(self.view.dashboard_total_units.text(), "0")
        self.assertEqual(self.view.dashboard_low_stock.text(), "0")
        self.assertEqual(self.view.dashboard_out_of_stock.text(), "0")
        self.assertIn("Net Movement: +0", self.view.movement_totals_label.text())


class _InventoryService:
    def __init__(self, items, transactions):
        self.items = items
        self.transactions = transactions

    def get_all_inventory(self):
        return self.items

    def get_all_transactions(self):
        return self.transactions

    def get_inventory(self, variant_id):
        return next(item for item in self.items if item["variant_id"] == variant_id)

    def issue_stock(self, variant_id, quantity, notes=None):
        self.last_issue = (variant_id, quantity, notes)
        return False


if __name__ == "__main__":
    unittest.main()
