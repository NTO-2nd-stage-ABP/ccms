import sys

from PyQt6.QtWidgets import QApplication

from app.db import ENGINE
from app.db.models import Base
from app.ui.main_window import MainWindow


def run() -> int:
    """
    Initializes the application and runs it.

    Returns:
        int: The exit status code.
    """
    app: QApplication = QApplication(sys.argv)

    Base.metadata.create_all(ENGINE)

    window: MainWindow = MainWindow()
    window.show()

    return sys.exit(app.exec())
