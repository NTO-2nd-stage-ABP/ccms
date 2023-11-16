import sys

from PyQt6.QtWidgets import QApplication

from app.config import APP_NAME
from app.db import ENGINE
from app.db.models import BaseModel
from app.ui.main_window import MainWindow


def run() -> int:
    """
    Initializes the application and runs it.

    Returns:
        int: The exit status code.
    """
    BaseModel.metadata.create_all(ENGINE)

    app: QApplication = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window: MainWindow = MainWindow()
    window.show()

    return sys.exit(app.exec())
