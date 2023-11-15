from PyQt6.QtWidgets import QMainWindow

from app.config import APP_NAME


class MainWindow(QMainWindow):
    """
    MainWindow

    Args:
        QMainWindow (QMainWindow): Inheritance
    """

    def __init__(self) -> None:
        """
        Initialize the Main-Window.
        """
        super().__init__()

        self.resize(800, 600)
        self.setWindowTitle(APP_NAME)
