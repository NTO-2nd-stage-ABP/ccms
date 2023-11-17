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
        uic.loadUi("app/ui/main_window.ui", self)

        self.statusbar.showMessage("Выберите элемент")
        self.create_action.triggered.connect(self.onCreateActionTriggered)
        self.events_type_manager_action.triggered.connect(self.onEventsTypeManagerActionTriggered)

    def onEventsTypeManagerActionTriggered(self):
        uic.loadUi("app/ui/dialogs/events_type_manager.ui").exec()

    def onCreateActionTriggered(self):
        uic.loadUi("app/ui/dialogs/event_edit.ui").exec()
