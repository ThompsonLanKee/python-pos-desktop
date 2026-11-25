
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class CheckoutDialog(QDialog):
    """Collect payment details for a POS checkout."""

    CASH_DENOMINATIONS = (20_000, 10_000, 5_000, 1_000, 500, 200, 100, 50)

    def __init__(self, total_amount: int, parent=None):
        super().__init__(parent)

        if total_amount <= 0:
            raise ValueError("Checkout total must be positive.")

        self.total_amount = int(total_amount)

        self.setWindowTitle("Complete Checkout")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        total_label = QLabel(
            f"Amount Due: {self.total_amount:,} MMK"
        )
        total_label.setObjectName("checkout_total")
        layout.addWidget(total_label)

        form = QFormLayout()

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem("Cash", "CASH")
        self.payment_method_combo.addItem("Card", "CARD")
        self.payment_method_combo.addItem(
            "Mobile Payment", "MOBILE"
        )
        self.payment_method_combo.addItem(
            "Bank Transfer", "BANK_TRANSFER"
        )
        self.payment_method_combo.addItem("Other", "OTHER")

        self.cash_received_spin = QSpinBox()
        self.cash_received_spin.setRange(0, 2_000_000_000)
        self.cash_received_spin.setValue(self.total_amount)
        self.cash_received_spin.setGroupSeparatorShown(True)

        self.denomination_spins = {}
        self._updating_from_denominations = False
        self.cash_denominations_group = QGroupBox("Cash denominations")
        denominations_layout = QGridLayout(
            self.cash_denominations_group
        )
        denominations_layout.setSpacing(8)

        for index, denomination in enumerate(self.CASH_DENOMINATIONS):
            note = QPushButton(f"{denomination:,} MMK")
            note.setObjectName("cash_note_button")
            note.setMinimumHeight(42)
            note.clicked.connect(
                lambda checked=False, value=denomination: self._add_note(
                    value
                )
            )

            quantity = QSpinBox()
            quantity.setRange(0, 1_000_000)
            quantity.setPrefix("Qty ")
            quantity.setToolTip(
                f"Number of {denomination:,} MMK notes"
            )
            quantity.valueChanged.connect(
                self._update_cash_from_denominations
            )
            self.denomination_spins[denomination] = quantity

            note_layout = QVBoxLayout()
            note_layout.setSpacing(4)
            note_layout.addWidget(note)
            note_layout.addWidget(quantity)

            note_widget = QGroupBox()
            note_widget.setLayout(note_layout)
            denominations_layout.addWidget(
                note_widget,
                index // 4,
                index % 4,
            )

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText(
            "Optional transaction/reference number"
        )

        form.addRow("Payment Method", self.payment_method_combo)
        form.addRow("Cash Received", self.cash_received_spin)
        form.addRow("Reference Number", self.reference_input)

        layout.addLayout(form)
        layout.addWidget(self.cash_denominations_group)

        self.change_label = QLabel("Change: 0 MMK")
        self.change_label.setObjectName("checkout_change")
        layout.addWidget(self.change_label)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("checkout_validation")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        layout.addWidget(self.validation_label)

        self.payment_method_combo.currentIndexChanged.connect(
            self._update_payment_fields
        )
        self.cash_received_spin.valueChanged.connect(
            self._cash_received_manually_changed
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )

        buttons.button(
            QDialogButtonBox.StandardButton.Ok
        ).setText("Confirm Payment")

        buttons.accepted.connect(self._confirm_payment)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setStyleSheet("""
            QDialog {
                background-color: #F5F7F5;
                color: #26352C;
            }

            QGroupBox {
                color: #315D40;
                font-weight: bold;
                border: 1px solid #DCE5DE;
                border-radius: 6px;
                margin-top: 8px;
                padding: 8px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }

            QLabel {
                color: #26352C;
            }

            QLabel#checkout_total {
                color: #203D2E;
                font-size: 20px;
                font-weight: bold;
                padding: 8px 0;
            }

            QLabel#checkout_change {
                color: #315D40;
                font-size: 15px;
                font-weight: bold;
            }

            QLabel#checkout_validation {
                color: #A94442;
                font-weight: bold;
            }

            QComboBox, QLineEdit, QSpinBox {
                background-color: white;
                border: 1px solid #DCE5DE;
                border-radius: 6px;
                padding: 8px;
                min-height: 24px;
            }

            QPushButton#cash_note_button {
                background-color: #E4EEE7;
                color: #203D2E;
                border: 1px solid #B8CDBE;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton#cash_note_button:hover {
                background-color: #D6EBDD;
            }

            QDialogButtonBox QPushButton {
                background-color: #EAF1EC;
                color: #203D2E;
                border: 1px solid #D0DDD4;
                border-radius: 6px;
                padding: 8px 14px;
                min-width: 90px;
            }
        """)

        self._update_payment_fields()

    def _update_payment_fields(self):
        is_cash = (
            self.payment_method_combo.currentData() == "CASH"
        )

        self.cash_received_spin.setVisible(is_cash)
        self.cash_denominations_group.setVisible(is_cash)
        self.change_label.setVisible(is_cash)

        self._update_change()

    def _add_note(self, denomination: int):
        quantity = self.denomination_spins[denomination]
        quantity.setValue(quantity.value() + 1)

    def _update_cash_from_denominations(self):
        if self._updating_from_denominations:
            return

        total_received = sum(
            denomination * quantity.value()
            for denomination, quantity in self.denomination_spins.items()
        )

        self._updating_from_denominations = True
        self.cash_received_spin.setValue(total_received)
        self._updating_from_denominations = False
        self.validation_label.hide()
        self._update_change()

    def _cash_received_manually_changed(self):
        if not self._updating_from_denominations:
            self._updating_from_denominations = True
            for quantity in self.denomination_spins.values():
                quantity.setValue(0)
            self._updating_from_denominations = False

        self.validation_label.hide()
        self._update_change()

    def _update_change(self):
        received = self.cash_received_spin.value()
        change = max(0, received - self.total_amount)

        self.change_label.setText(
            f"Change: {change:,} MMK"
        )

    def _confirm_payment(self):
        if (
            self.payment_method_combo.currentData() == "CASH"
            and self.cash_received_spin.value() < self.total_amount
        ):
            self.validation_label.setText(
                "Cash received must cover the amount due."
            )
            self.validation_label.show()
            return

        self.accept()

    def get_payment_data(self):
        return {
            "payment_method": self.payment_method_combo.currentData(),
            "amount": self.total_amount,
            "reference_number": (
                self.reference_input.text().strip() or None
            ),
            "notes": None,
        }

    def get_change_amount(self):
        if self.payment_method_combo.currentData() != "CASH":
            return 0

        return max(
            0,
            self.cash_received_spin.value() - self.total_amount
        )
