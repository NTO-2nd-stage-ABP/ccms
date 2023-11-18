from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QTableView, QAbstractItemView

from app.ui.dialogs import TypeManagerDialog, CreateActionDialog
from app.utils.views import EventsTableModel


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
        self.refreshTables()
        self.statusbar.showMessage("Выберите элемент")
        self.create_action.triggered.connect(self.onCreateActionTriggered)
        self.events_type_manager_action.triggered.connect(self.onEventsTypeManagerActionTriggered)
        self.delete_action.triggered.connect(self.deleteEvent)
        
        self.entertainmentView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.entertainmentView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        self.enlightenmentView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.enlightenmentView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def refreshTables(self):
        self.model = EventsTableModel()
        self.entertainmentView.setModel(self.model)
        self.enlightenmentView.setModel(self.model)

    def deleteEvent(self):
        if not self.entertainmentView.selectedIndexes() and not self.enlightenmentView.selectedIndexes():
            return
        self.model.removeRow(self.entertainmentView.selectedIndexes()[0].row())

    def onEventsTypeManagerActionTriggered(self):
        dlg = TypeManagerDialog()
        dlg.exec()

    def onCreateActionTriggered(self):
        dlg = CreateActionDialog(self.tabWidget.currentIndex())
        dlg.exec()
        self.refreshTables()
