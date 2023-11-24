from typing import Set
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QHeaderView

from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import (
    EventType,
    RoomType,
    WorkRequest,
    WorkRequestType,
    WorkRequestStatus,
)
from app.ui.dialogs import (
    TypeManagerDialog,
    CreateEventDialog,
    EditEventDialog,
    CreateWorkDialog,
)
from app.ui.dialogs.ext import EditWorksDialog
from app.ui.models import EventTableModel, WorkTableModel


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

        self.refreshTableViews()
        self.eventsTableView.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.worksTableView.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.desktopTableView.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

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
            lambda: TypeManagerDialog(WorkRequestType, "Виды работ:").exec()
        )
        
    def refreshDesktop(self):
        with Session(ENGINE) as session:
            workRequests: Set[WorkRequest] = session.exec(select(WorkRequest)).all()
            self.desktopTableModel = WorkTableModel(
                list(
                    filter(
                        lambda request: request.status == WorkRequestStatus.ACTIVE,
                        workRequests,
                    )
                )
            )
        self.desktopTableView.setModel(self.desktopTableModel)
        self.desktopTableView.selectionModel().selectionChanged.connect(
            self.onDesktopTableViewSelectionChanged
        )
        

    def refreshTableViews(self):
        self.eventsTableModel = EventTableModel()
        with Session(ENGINE) as session:
            workRequests: Set[WorkRequest] = session.exec(select(WorkRequest)).all()
            self.worksTableModel = WorkTableModel(workRequests)
            self.desktopTableModel = WorkTableModel(
                list(
                    filter(
                        lambda request: request.status == WorkRequestStatus.ACTIVE,
                        workRequests,
                    )
                )
            )

        self.eventsTableView.setModel(self.eventsTableModel)
        self.worksTableView.setModel(self.worksTableModel)
        self.desktopTableView.setModel(self.desktopTableModel)

        self.eventsTableView.selectionModel().selectionChanged.connect(
            self.onEventsTableViewSelectionChanged
        )
        self.worksTableView.selectionModel().selectionChanged.connect(
            self.onWorkTableViewSelectionChanged
        )
        self.desktopTableView.selectionModel().selectionChanged.connect(
            self.onDesktopTableViewSelectionChanged
        )

        self.eventsTableView.doubleClicked.connect(
            self.onEditSelectedEventsPushButtonClicked
        )
        self.worksTableView.doubleClicked.connect(
            self.onEditSelectedWorksPushButtonClicked
        )

    def onNewEventPushButtonClicked(self):
        dlg = CreateEventDialog()
        dlg.exec()
        self.refreshTableViews()

    def onEditSelectedEventsPushButtonClicked(self):
        index = self.eventsTableView.selectedIndexes()[0].row()
        dlg = EditEventDialog(self.eventsTableModel.ddata[index])
        dlg.exec()

    def onEditSelectedWorksPushButtonClicked(self):
        index = self.worksTableView.selectedIndexes()[0].row()
        dlg = EditWorksDialog(self.worksTableModel.ddata[index])
        dlg.exec()
        self.refreshDesktop()

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
        selectedIndexesCount = len(
            self.desktopTableView.selectionModel().selectedRows()
        )
        self.selectedDesktopCountLabel.setText(
            f"{selectedIndexesCount} из {self.desktopTableModel.rowCount()} выбрано"
        )
        self.completeSelectedDesktopPushButton.setEnabled(selectedIndexesCount)

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
        with Session(ENGINE) as session:    
            for index in self.desktopTableView.selectionModel().selectedRows():
                item: WorkRequest = self.desktopTableModel.ddata[index.row()]
                workRequest: WorkRequest = session.get(WorkRequest, item.id)
                workRequest.status = WorkRequestStatus.COMPLETED
                session.add(workRequest)
                self.desktopTableModel.removeRow(index.row(), delete=False)
            session.commit()
        self.refreshTableViews()

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
        self.refreshTableViews()


__all__ = ["MainWindow"]
