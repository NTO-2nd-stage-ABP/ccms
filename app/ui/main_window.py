from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow

from app.ui.dialogs import TypeManagerDialog, CreateActionDialog


class MainWindow(QMainWindow):
    """
    Represents the Main-Window of this application.
    """

    def __init__(self) -> None:
        """
        Initialize the Main-Window.
        """
        super().__init__()
        uic.loadUi("app/ui/main_window.ui", self)

        self.statusbar.showMessage("Выберите элемент")
        self.create_action.triggered.connect(self.onCreateActionTriggered)
        self.events_type_manager_action.triggered.connect(self.onEventsTypeManagerActionTriggered)

    def onEventsTypeManagerActionTriggered(self):
        dlg = TypeManagerDialog()
        dlg.exec()

    def onCreateActionTriggered(self):
        dlg = CreateActionDialog()
        dlg.exec()
