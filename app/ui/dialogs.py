from PyQt6 import uic
from PyQt6.QtWidgets import QDialog

from app.utils.views import EventTypesListModel


class TypeManagerDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("app/ui/dialogs/events_type_manager.ui", self)

        self.listViewModel = EventTypesListModel(self)
        self.listView.setModel(self.listViewModel)

        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)
        
    def onAddButtonClicked(self) -> None:
        self.listViewModel.insertRow(-1)
        
    def onDelButtonClicked(self) -> None:
        currentRowIndex = self.listView.currentIndex().row()
        self.listViewModel.removeRow(currentRowIndex)


class CreateActionDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/event_edit.ui", self)
