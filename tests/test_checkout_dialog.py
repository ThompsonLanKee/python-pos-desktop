import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from src.views.checkout_dialog import CheckoutDialog


class CheckoutDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_denomination_quantities_calculate_cash_received_and_change(self):
        dialog = CheckoutDialog(total_amount=6_000)

        dialog.denomination_spins[1_000].setValue(6)

        self.assertEqual(dialog.cash_received_spin.value(), 6_000)
        self.assertEqual(dialog.get_change_amount(), 0)
        self.assertEqual(dialog.get_payment_data()["amount"], 6_000)

    def test_note_button_adds_one_note_and_calculates_change(self):
        dialog = CheckoutDialog(total_amount=6_000)

        note_button = next(
            button
            for button in dialog.cash_group.findChildren(
                QPushButton
            )
            if button.text() == "10,000 MMK"
        )
        note_button.click()

        self.assertEqual(dialog.denomination_spins[10_000].value(), 1)
        self.assertEqual(dialog.cash_received_spin.value(), 10_000)
        self.assertEqual(dialog.get_change_amount(), 4_000)

    def test_manual_cash_entry_clears_denomination_quantities(self):
        dialog = CheckoutDialog(total_amount=6_000)
        dialog.denomination_spins[1_000].setValue(6)

        dialog.cash_received_spin.setValue(10_000)

        self.assertEqual(dialog.denomination_spins[1_000].value(), 0)
        self.assertEqual(dialog.get_change_amount(), 4_000)

    def test_cash_underpayment_cannot_confirm(self):
        dialog = CheckoutDialog(total_amount=6_000)
        dialog.denomination_spins[1_000].setValue(5)

        dialog._confirm_payment()

        self.assertEqual(dialog.result(), dialog.DialogCode.Rejected)
        self.assertFalse(dialog.validation_label.isHidden())


if __name__ == "__main__":
    unittest.main()
