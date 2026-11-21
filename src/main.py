import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("POS Desktop Application")
        self.setMinimumSize(900, 600)

        label = QLabel("Welcome to POS Development!")

        self.setCentralWidget(label)


def main():

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()