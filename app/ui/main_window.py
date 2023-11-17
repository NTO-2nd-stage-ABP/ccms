from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    """
    Represents the Main-Window of this application.
    """

    def __init__(self) -> None:
        """
        Initialize the Main-Window.
        """
        super().__init__()
        uic.loadUi('app/ui/main_window.ui', self)
        # self.resize(800, 600)
