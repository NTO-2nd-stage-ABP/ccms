from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QTableView, QAbstractItemView, QMessageBox

from app.db.models import EventType, RoomType, WorkType
from app.ui.models import EventTableModel
from app.ui.dialogs import (
    TypeManagerDialog,
    CreateEventDialog,
    EditEventDialog,
    CreateWorkDialog,
)


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

        self.refreshEventsTable()
        self.newEventPushButton.clicked.connect(self.onNewEventPushButtonClicked)
        self.editSelectedEventsPushButton.clicked.connect(
            self.onEditSelectedEventsPushButtonClicked
        )
        self.deleteSelectedEventsPushButton.clicked.connect(
            self.onDeleteSelectedEventsPushButtonClicked
        )
        self.newWorkPushButton.clicked.connect(self.onNewWorkPushButtonClicked)

        self.eventsTypeMaximizeToolButton.clicked.connect(
            lambda: TypeManagerDialog(EventType, "Виды мероприятий:").exec()
        )
        self.roomsMaximizeToolButton.clicked.connect(
            lambda: TypeManagerDialog(RoomType, "Помещения:").exec()
        )
        self.worksTypeMaximizeToolButton.clicked.connect(
            lambda: TypeManagerDialog(WorkType, "Виды работ:").exec()
        )

    def refreshEventsTable(self):
        self.eventsTableModel = EventTableModel()
        self.eventsTableView.setModel(self.eventsTableModel)
        self.eventsTableView.selectionModel().selectionChanged.connect(
            self.onEventsTableViewSelectionChanged
        )
        self.eventsTableView.doubleClicked.connect(
            self.onEditSelectedEventsPushButtonClicked
        )

    def onNewEventPushButtonClicked(self):
        dlg = CreateEventDialog(self.tabWidget.currentIndex())
        dlg.exec()
        self.refreshEventsTable()

    def onEditSelectedEventsPushButtonClicked(self):
        index = self.eventsTableView.selectedIndexes()[0].row()
        dlg = EditEventDialog(self.eventsTableModel.ddata[index])
        dlg.exec()

    def onEventsTableViewSelectionChanged(self):
        selectedIndexesCount = len(self.eventsTableView.selectionModel().selectedRows())
        self.selectedEventsCountLabel.setText(
            f"{selectedIndexesCount} из {self.eventsTableModel.rowCount()} выбрано"
        )
        self.deleteSelectedEventsPushButton.setEnabled(selectedIndexesCount)
        self.editSelectedEventsPushButton.setEnabled(selectedIndexesCount == 1)

    def onDeleteSelectedEventsPushButtonClicked(self):
        if self.showConfirmationWarning() != QMessageBox.StandardButton.Ok:
            return False

        for index in self.eventsTableView.selectionModel().selectedRows():
            self.eventsTableModel.removeRow(index.row())

    def showConfirmationWarning(self):
        return QMessageBox.warning(
            self.parent(),
            "Удаление объектов",
            "Вы действительно хотите удалить выбранные объекты?",
            defaultButton=QMessageBox.StandardButton.Cancel,
        )

    def onNewWorkPushButtonClicked(self):
        dlg = CreateWorkDialog()
        dlg.exec()


__all__ = ["MainWindow"]
