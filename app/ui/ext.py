from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QHeaderView

from app.db.models import EventType, RoomType, WorkType
from app.ui.dialogs import (
    TypeManagerDialog,
    CreateEventDialog,
    EditEventDialog,
    CreateWorkDialog,
)
from app.ui.dialogs.ext import EditWorksDialog
from app.ui.models import EventTableModel, WorkTableModel, DesktopTableModel


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
        self.eventsTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.worksTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.desktopTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.newEventPushButton.clicked.connect(self.onNewEventPushButtonClicked)
        self.editSelectedEventsPushButton.clicked.connect(
            self.onEditSelectedEventsPushButtonClicked
        )
        self.deleteSelectedEventsPushButton.clicked.connect(
            self.onDeleteSelectedEventsPushButtonClicked
        )

        self.newWorkPushButton.clicked.connect(self.onNewWorkPushButtonClicked)
        self.editSelectedWorksPushButton.clicked.connect(
            self.onEditSelectedWorksPushButtonClicked
        )
        self.deleteSelectedWorksPushButton.clicked.connect(
            self.onDeleteSelectedWorksPushButtonClicked
        )
        self.completeSelectedDesktopPushButton.clicked.connect(
            self.onCompleteSelectedWorksPushButtonClicked
        )

        self.eventsTypeMaximizeToolButton.clicked.connect(
            lambda: TypeManagerDialog(EventType, "Виды мероприятий:").exec()
        )
        self.roomsMaximizeToolButton.clicked.connect(
            lambda: TypeManagerDialog(RoomType, "Помещения:").exec()
        )
        self.roomsMaximizeToolButton_2.clicked.connect(
            lambda: TypeManagerDialog(RoomType, "Помещения:").exec()
        )
        self.worksTypeMaximizeToolButton.clicked.connect(
            lambda: TypeManagerDialog(WorkType, "Виды работ:").exec()
        )

    def refreshEventsTable(self):
        self.eventsTableModel = EventTableModel()
        self.worksTableModel = WorkTableModel()
        self.desktopTableModel = DesktopTableModel()

        self.eventsTableView.setModel(self.eventsTableModel)
        self.worksTableView.setModel(self.worksTableModel)
        self.desktopTableView.setModel(self.desktopTableModel)

        self.eventsTableView.selectionModel().selectionChanged.connect(self.onEventsTableViewSelectionChanged)
        self.worksTableView.selectionModel().selectionChanged.connect(self.onWorkTableViewSelectionChanged)
        self.desktopTableView.selectionModel().selectionChanged.connect(self.onDesktopTableViewSelectionChanged)

        self.eventsTableView.doubleClicked.connect(self.onEditSelectedEventsPushButtonClicked)
        self.worksTableView.doubleClicked.connect(self.onEditSelectedWorksPushButtonClicked)
        # self.desktopTableView.doubleClicked.connect(self.onEditSelectedWorksPushButtonClicked)


    def onNewEventPushButtonClicked(self):
        dlg = CreateEventDialog()
        dlg.exec()
        self.refreshEventsTable()


    def onEditSelectedEventsPushButtonClicked(self):
        index = self.eventsTableView.selectedIndexes()[0].row()
        dlg = EditEventDialog(self.eventsTableModel.ddata[index])
        dlg.exec()

    def onEditSelectedWorksPushButtonClicked(self):
        index = self.worksTableView.selectedIndexes()[0].row()
        dlg = EditWorksDialog(self.worksTableModel.ddata[index])
        dlg.exec()
        self.refreshEventsTable()

    def onEventsTableViewSelectionChanged(self):
        selectedIndexesCount = len(self.eventsTableView.selectionModel().selectedRows())
        self.selectedEventsCountLabel.setText(
            f"{selectedIndexesCount} из {self.eventsTableModel.rowCount()} выбрано"
        )
        self.deleteSelectedEventsPushButton.setEnabled(selectedIndexesCount)
        self.editSelectedEventsPushButton.setEnabled(selectedIndexesCount == 1)

    def onWorkTableViewSelectionChanged(self):
        selectedIndexesCount = len(self.worksTableView.selectionModel().selectedRows())
        self.selectedWorkCountLabel.setText(
            f"{selectedIndexesCount} из {self.worksTableModel.rowCount()} выбрано"
        )
        self.deleteSelectedWorksPushButton.setEnabled(selectedIndexesCount)
        self.editSelectedWorksPushButton.setEnabled(selectedIndexesCount == 1)

    def onDesktopTableViewSelectionChanged(self):
        selectedIndexesCount = len(self.desktopTableView.selectionModel().selectedRows())
        self.selectedDesktopCountLabel.setText(
            f"{selectedIndexesCount} из {self.desktopTableModel.rowCount()} выбрано"
        )
        self.completeSelectedDesktopPushButton.setEnabled(selectedIndexesCount)
        # self.editSelectedWorksPushButton.setEnabled(selectedIndexesCount == 1)

    def onDeleteSelectedEventsPushButtonClicked(self):
        if self.showConfirmationWarning() != QMessageBox.StandardButton.Ok:
            return False

        for index in self.eventsTableView.selectionModel().selectedRows():
            self.eventsTableModel.removeRow(index.row())

    def onDeleteSelectedWorksPushButtonClicked(self):
        if self.showConfirmationWarning() != QMessageBox.StandardButton.Ok:
            return False

        for index in self.worksTableView.selectionModel().selectedRows():
            self.worksTableModel.removeRow(index.row())
    def onCompleteSelectedWorksPushButtonClicked(self):
        if self.showConfirmationWarningComplete() != QMessageBox.StandardButton.Ok:
            return False

        for index in self.desktopTableView.selectionModel().selectedRows():
            self.desktopTableModel.removeRow(index.row())
        self.refreshEventsTable()

    def showConfirmationWarning(self):
        return QMessageBox.warning(
            self.parent(),
            "Удаление объектов",
            "Вы действительно хотите удалить выбранные объекты?",
            defaultButton=QMessageBox.StandardButton.Cancel,
        )

    def showConfirmationWarningComplete(self):
        return QMessageBox.warning(
            self.parent(),
            "Выполнение задач",
            "Вы действительно хотите отметить эти задачи выполнеными?",
            defaultButton=QMessageBox.StandardButton.Cancel,
        )

    def onNewWorkPushButtonClicked(self):
        dlg = CreateWorkDialog()
        dlg.exec()
        self.refreshEventsTable()


__all__ = ["MainWindow"]
