from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)


class CheckoutDialog(QDialog):
    """Collect payment details for a POS checkout."""

    CASH_DENOMINATIONS = (20_000, 10_000, 5_000, 1_000, 500, 200, 100, 50)

    def __init__(self, total_amount: int, parent=None):
        super().__init__(parent)
        if isinstance(total_amount, bool) or int(total_amount) <= 0:
            raise ValueError("Checkout total must be positive.")

        self.total_amount = int(total_amount)
        self._updating_from_denominations = False
        self.denomination_spins = {}
        self.denomination_buttons = {}
        project_root = Path(__file__).resolve().parents[2]
        self.cash_image_directory = project_root / "data" / "cash_denominations"

        self.setWindowTitle("Complete Checkout")
        self.setModal(True)
        self.setMinimumSize(620, 620)
        self.resize(700, 720)
        self._build_ui()
        self._connect_signals()
        self._update_payment_fields()
        self._update_change()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(13)

        amount_panel = QWidget()
        amount_panel.setObjectName("amount_panel")
        amount_layout = QVBoxLayout(amount_panel)
        amount_layout.setContentsMargins(16, 12, 16, 12)
        caption = QLabel("AMOUNT DUE")
        caption.setObjectName("amount_caption")
        total = QLabel(f"{self.total_amount:,} MMK")
        total.setObjectName("checkout_total")
        amount_layout.addWidget(caption)
        amount_layout.addWidget(total)
        root.addWidget(amount_panel)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        self.payment_method_combo = QComboBox()
        for label, code in (
            ("Cash", "CASH"), ("Card", "CARD"),
            ("Mobile Payment", "MOBILE"),
            ("Bank Transfer", "BANK_TRANSFER"), ("Other", "OTHER"),
        ):
            self.payment_method_combo.addItem(label, code)
        self.payment_method_combo.setMinimumHeight(40)

        self.reference_label = QLabel("Reference Number")
        self.reference_input = QLineEdit()
        self.reference_input.setMinimumHeight(40)
        self.reference_input.setPlaceholderText("Optional transaction/reference number")
        form.addRow("Payment Method", self.payment_method_combo)
        form.addRow(self.reference_label, self.reference_input)
        root.addLayout(form)

        self.cash_group = QGroupBox("Cash payment")
        cash_layout = QVBoxLayout(self.cash_group)
        cash_layout.setContentsMargins(13, 17, 13, 12)
        cash_layout.setSpacing(10)

        self.cash_received_spin = QSpinBox()
        self.cash_received_spin.setRange(0, 2_000_000_000)
        self.cash_received_spin.setValue(self.total_amount)
        self.cash_received_spin.setGroupSeparatorShown(True)
        self.cash_received_spin.setSuffix(" MMK")
        self.cash_received_spin.setMinimumHeight(40)
        cash_form = QFormLayout()
        cash_form.addRow("Cash Received", self.cash_received_spin)
        cash_layout.addLayout(cash_form)

        heading_row = QHBoxLayout()
        heading = QLabel("Select banknotes")
        heading.setObjectName("section_heading")
        hint = QLabel("Tap a note to add one")
        hint.setObjectName("muted_text")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        heading_row.addWidget(hint)
        cash_layout.addLayout(heading_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setMinimumHeight(220)
        scroll.setMaximumHeight(275)
        note_container = QWidget()
        notes_grid = QGridLayout(note_container)
        notes_grid.setContentsMargins(2, 2, 2, 2)
        notes_grid.setSpacing(9)

        for index, denomination in enumerate(self.CASH_DENOMINATIONS):
            card = QWidget()
            card.setObjectName("note_card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 6, 6, 6)
            card_layout.setSpacing(5)

            button = QPushButton()
            button.setObjectName("cash_note_button")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(75)
            button.setIconSize(QSize(145, 48))
            button.setToolTip(f"Add one {denomination:,} MMK banknote")
            image_path = self.cash_image_directory / f"{denomination}ks.png"
            if image_path.is_file():
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    button.setIcon(QIcon(pixmap))
            button.setText(f"{denomination:,} MMK")
            button.clicked.connect(lambda checked=False, value=denomination: self._add_note(value))

            quantity = QSpinBox()
            quantity.setRange(0, 1_000_000)
            quantity.setPrefix("Qty: ")
            quantity.setAlignment(Qt.AlignmentFlag.AlignCenter)
            quantity.valueChanged.connect(self._update_cash_from_denominations)
            self.denomination_spins[denomination] = quantity
            self.denomination_buttons[denomination] = button
            card_layout.addWidget(button)
            card_layout.addWidget(quantity)
            notes_grid.addWidget(card, index // 2, index % 2)

        scroll.setWidget(note_container)
        cash_layout.addWidget(scroll)

        footer = QHBoxLayout()
        self.selected_notes_label = QLabel("Selected notes total: 0 MMK")
        self.selected_notes_label.setObjectName("muted_text")
        self.clear_notes_button = QPushButton("Clear Notes")
        self.clear_notes_button.setObjectName("secondary_button")
        self.clear_notes_button.clicked.connect(self._clear_notes)
        footer.addWidget(self.selected_notes_label)
        footer.addStretch()
        footer.addWidget(self.clear_notes_button)
        cash_layout.addLayout(footer)
        root.addWidget(self.cash_group)

        self.change_label = QLabel("Change: 0 MMK")
        self.change_label.setObjectName("checkout_change")
        root.addWidget(self.change_label)
        self.validation_label = QLabel()
        self.validation_label.setObjectName("checkout_validation")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        root.addWidget(self.validation_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        self.confirm_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.confirm_button.setText("Confirm Payment")
        self.confirm_button.setObjectName("confirm_button")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        root.addWidget(self.buttons)

        self.setStyleSheet("""
            QDialog { background: #F5F7F5; color: #26352C; font-family: "Segoe UI"; font-size: 13px; }
            QWidget#amount_panel { background: #E8F0EA; border: 1px solid #D5E2D8; border-radius: 10px; }
            QLabel#amount_caption { color: #668071; font-size: 10px; font-weight: bold; letter-spacing: 1px; }
            QLabel#checkout_total { color: #203D2E; font-size: 25px; font-weight: bold; }
            QGroupBox { color: #315D40; font-size: 14px; font-weight: bold; border: 1px solid #DCE5DE; border-radius: 9px; margin-top: 9px; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QLabel { color: #26352C; }
            QLabel#section_heading { color: #315D40; font-weight: bold; }
            QLabel#muted_text { color: #78877E; font-size: 11px; }
            QLabel#checkout_change { color: #315D40; font-size: 16px; font-weight: bold; }
            QLabel#checkout_validation { color: #A94442; font-weight: bold; }
            QComboBox, QLineEdit, QSpinBox { background: white; color: #26352C; border: 1px solid #D5E0D8; border-radius: 6px; padding: 7px 9px; min-height: 24px; }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus { border: 1px solid #5D8B6B; }
            QWidget#note_card { background: white; border: 1px solid #DFE8E1; border-radius: 7px; }
            QPushButton#cash_note_button { background: #F1F6F2; color: #203D2E; border: 1px solid #D6E3D9; border-radius: 5px; font-weight: bold; padding: 5px; }
            QPushButton#cash_note_button:hover { background: #E2EEE5; border: 1px solid #9FBEA8; }
            QPushButton#secondary_button, QDialogButtonBox QPushButton { background: #EAF1EC; color: #203D2E; border: 1px solid #D0DDD4; border-radius: 6px; padding: 8px 15px; min-width: 85px; }
            QPushButton#confirm_button { background: #315D40; color: white; border: none; border-radius: 6px; padding: 9px 18px; min-width: 125px; font-weight: bold; }
            QPushButton#confirm_button:hover { background: #264C34; }
            QScrollArea { background: transparent; }
        """)

    def _connect_signals(self):
        self.payment_method_combo.currentIndexChanged.connect(self._update_payment_fields)
        self.cash_received_spin.valueChanged.connect(self._cash_received_manually_changed)
        self.buttons.accepted.connect(self._confirm_payment)
        self.buttons.rejected.connect(self.reject)

    def _update_payment_fields(self):
        is_cash = self.payment_method_combo.currentData() == "CASH"
        self.cash_group.setVisible(is_cash)
        self.change_label.setVisible(is_cash)
        self.reference_label.setVisible(not is_cash)
        self.reference_input.setVisible(not is_cash)
        if is_cash:
            self.reference_input.clear()
        self.validation_label.hide()
        self._update_change()

    def _add_note(self, denomination: int):
        spin = self.denomination_spins[denomination]
        spin.setValue(spin.value() + 1)

    def _update_cash_from_denominations(self):
        if self._updating_from_denominations:
            return
        received = sum(value * spin.value() for value, spin in self.denomination_spins.items())
        self._updating_from_denominations = True
        self.cash_received_spin.setValue(received)
        self._updating_from_denominations = False
        self.selected_notes_label.setText(f"Selected notes total: {received:,} MMK")
        self.validation_label.hide()
        self._update_change()

    def _cash_received_manually_changed(self):
        if not self._updating_from_denominations:
            self._updating_from_denominations = True
            for spin in self.denomination_spins.values():
                spin.setValue(0)
            self._updating_from_denominations = False
            self.selected_notes_label.setText("Manual cash entry")
        self.validation_label.hide()
        self._update_change()

    def _clear_notes(self):
        self._updating_from_denominations = True
        for spin in self.denomination_spins.values():
            spin.setValue(0)
        self.cash_received_spin.setValue(0)
        self._updating_from_denominations = False
        self.selected_notes_label.setText("Selected notes total: 0 MMK")
        self.validation_label.hide()
        self._update_change()

    def _update_change(self):
        change = max(0, self.cash_received_spin.value() - self.total_amount)
        self.change_label.setText(f"Change: {change:,} MMK")

    def _confirm_payment(self):
        if (self.payment_method_combo.currentData() == "CASH"
                and self.cash_received_spin.value() < self.total_amount):
            self.validation_label.setText("Cash received must cover the amount due.")
            self.validation_label.show()
            return
        self.accept()

    def get_payment_data(self):
        return {
            "payment_method": self.payment_method_combo.currentData(),
            # Record the sale amount, not the cash tendered.
            "amount": self.total_amount,
            "reference_number": self.reference_input.text().strip() or None,
            "notes": None,
        }

    def get_change_amount(self):
        if self.payment_method_combo.currentData() != "CASH":
            return 0
        return max(0, self.cash_received_spin.value() - self.total_amount)
