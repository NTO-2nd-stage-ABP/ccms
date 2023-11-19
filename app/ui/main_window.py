from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QTableView, QAbstractItemView, QMessageBox

from app.ui.dialogs import TypeManagerDialog, EditActionDialog, EditEventActionDialog
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
        self.edit_action.triggered.connect(self.editEvent)
        
        self.entertainmentView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.entertainmentView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.entertainmentView.doubleClicked.connect(self.editEvent)
        self.entertainmentView.selectionModel().selectionChanged.connect(self.removeStatusBarMessage)
        
        self.enlightenmentView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.enlightenmentView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.enlightenmentView.doubleClicked.connect(self.editEvent)
        self.enlightenmentView.selectionModel().selectionChanged.connect(self.removeStatusBarMessage)
        
    def removeStatusBarMessage(self):
        self.statusbar.clearMessage()

    def refreshTables(self):
        self.model = EventsTableModel()
        self.entertainmentView.setModel(self.model)
        self.enlightenmentView.setModel(self.model)

    def deleteEvent(self):
        if self.tabWidget.currentIndex() == 2:
            QMessageBox.warning(self, "Ошибка", "Действия в этом разделе сейчас недоступны")
            return
        if not self.entertainmentView.selectedIndexes() and not self.enlightenmentView.selectedIndexes():
            QMessageBox.warning(self, "Ошибка проверки", "Выберете строку таблицы для удаления мероприятия")
            return

        if self.tabWidget.currentIndex() == 0:
            self.model.removeRow(self.entertainmentView.selectedIndexes()[0].row())
        else:
            self.model.removeRow(self.enlightenmentView.selectedIndexes()[0].row())

    def editEvent(self):
        if self.tabWidget.currentIndex() == 2:
            QMessageBox.warning(self, "Ошибка", "Действия в этом разделе сейчас недоступны")
            return
        if not self.entertainmentView.selectedIndexes() and not self.enlightenmentView.selectedIndexes():
            QMessageBox.warning(self, "Ошибка проверки", "Выберете строку таблицы для редактирования мероприятия")
            return
        if self.tabWidget.currentIndex() == 0:
            index = self.entertainmentView.selectedIndexes()[0].row()
        else:
            index = self.enlightenmentView.selectedIndexes()[0].row()
        dlg = EditEventActionDialog(self.model.ddata[index])
        dlg.exec()

    def onEventsTypeManagerActionTriggered(self):
        dlg = TypeManagerDialog()
        dlg.exec()

    def onCreateActionTriggered(self):
        if self.tabWidget.currentIndex() != 2:
            dlg = EditActionDialog(self.tabWidget.currentIndex())
            dlg.exec()
            self.refreshTables()
        else:
            QMessageBox.warning(self, "Ошибка", "Действия в этом разделе сейчас недоступны")
            return
