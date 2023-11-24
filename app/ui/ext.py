from typing import Set
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QWidget, QTableView

from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import (
    Event,
    EventType,
    RoomType,
    WorkRequest,
    WorkRequestType,
)
from app.ui.dialogs import (
    TypeManagerDialog,
    CreateEventDialog,
    EditEventDialog,
    CreateWorkDialog,
)
from app.ui.dialogs.ext import EditWorksDialog
from app.ui.models import EventTableModel, WorkRequestTableModel


class Table(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        pass


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
        
        self.eventsTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.worksTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.desktopTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.refreshTableViews()
        
        self.eventsTypeMaximizePushButton.clicked.connect(lambda: self.showTypeManagerDialog(EventType, "Виды мероприятий:"))
        self.worksTypeMaximizePushButton.clicked.connect(lambda: self.showTypeManagerDialog(WorkRequestType, "Виды работ:"))
        self.action_2.triggered.connect(lambda: self.showTypeManagerDialog(RoomType, "Помещения:"))

        self.newEventPushButton.clicked.connect(lambda: self.onCreateClicked(CreateEventDialog()))
        self.newWorkPushButton.clicked.connect(lambda: self.onCreateClicked(CreateWorkDialog()))
        
        self.editSelectedEventsPushButton.clicked.connect(self.onEditSelectedEventsPushButtonClicked)
        self.editSelectedWorksPushButton.clicked.connect(self.onEditSelectedWorksPushButtonClicked)
        
        self.deleteSelectedEventsPushButton.clicked.connect(lambda: self.onDeleteRowsClicked(self.eventsTableView))
        self.deleteSelectedWorksPushButton.clicked.connect(lambda: self.onDeleteRowsClicked(self.worksTableView))

        self.completeSelectedDesktopPushButton.clicked.connect(self.onCompleteSelectedWorksPushButtonClicked)

        with Session(ENGINE) as session:
            workTypeNames = session.exec(select(WorkRequestType.name)).all()

        self.comboBox_12.addItems(workTypeName for workTypeName in workTypeNames)
        self.comboBox_12.currentTextChanged.connect(self.filterByWorkTypeName)
        self.resetDesktopFilterButton.clicked.connect(self.refreshDesktop)

    def showTypeManagerDialog(self, _type, title):
        TypeManagerDialog(_type, title).exec()
        self.refreshTableViews()

    def filterByWorkTypeName(self):
        name = self.comboBox_12.currentText()
        with Session(ENGINE) as session:
            type_id = session.exec(
                select(WorkRequestType.id).where(WorkRequestType.name == name)
            ).first()
        self.refreshDesktop(where=WorkRequest.type_id == type_id)

    def refreshDesktop(self, *args, where=None):
        with Session(ENGINE) as session:
            statement = select(WorkRequest).where(WorkRequest.status == WorkRequest.Status.ACTIVE)
            if where is not None:
                statement = statement.where(where)
            data: Set[WorkRequest] = session.exec(statement).all()

        self.desktopTableModel = WorkRequestTableModel(data)
        self.desktopTableView.setModel(self.desktopTableModel)
        self.desktopTableView.selectionModel().selectionChanged.connect(
            self.onDesktopTableViewSelectionChanged
        )
        self.completeSelectedDesktopPushButton.setEnabled(False)
        
    # def refreshWorkRequests(self, *args, where=None):

    def refreshTableViews(self):
        self.refreshDesktop()

        with Session(ENGINE) as session:
            events = session.exec(select(Event)).all()
            workRequests: Set[WorkRequest] = session.exec(select(WorkRequest)).all()
            self.worksTableModel = WorkRequestTableModel(workRequests)
            self.eventsTableModel = EventTableModel(events)

        self.eventsTableView.setModel(self.eventsTableModel)
        self.worksTableView.setModel(self.worksTableModel)

        self.eventsTableView.selectionModel().selectionChanged.connect(
            self.onEventsTableViewSelectionChanged
        )
        self.worksTableView.selectionModel().selectionChanged.connect(
            self.onWorkTableViewSelectionChanged
        )
        
        self.deleteSelectedEventsPushButton.setEnabled(False)
        self.editSelectedEventsPushButton.setEnabled(False)
        self.editSelectedWorksPushButton.setEnabled(False)
        self.deleteSelectedWorksPushButton.setEnabled(False)

    def onEditSelectedEventsPushButtonClicked(self):
        index = self.eventsTableView.selectedIndexes()[0].row()
        dlg = EditEventDialog(self.eventsTableModel._data[index])
        dlg.exec()

    def onEditSelectedWorksPushButtonClicked(self):
        index = self.worksTableView.selectedIndexes()[0].row()
        dlg = EditWorksDialog(self.worksTableModel._data[index])
        dlg.exec()
        self.refreshDesktop()

    def updateSelection(self, tableView, countLabel, tableModel, deleteButton, editButton):
        selectedIndexesCount = len(
            tableView.selectionModel().selectedRows()
        )
        countLabel.setText(
            f"{selectedIndexesCount} из {tableModel.rowCount()} выбрано"
        )
        deleteButton.setEnabled(selectedIndexesCount)
        if editButton:
            editButton.setEnabled(selectedIndexesCount == 1)

    def onEventsTableViewSelectionChanged(self):
        self.updateSelection(
            self.eventsTableView,
            self.selectedEventsCountLabel,
            self.eventsTableModel,
            self.deleteSelectedEventsPushButton,
            self.editSelectedEventsPushButton
        )

    def onWorkTableViewSelectionChanged(self):
        self.updateSelection(
            self.worksTableView,
            self.selectedWorkCountLabel,
            self.worksTableModel,
            self.deleteSelectedWorksPushButton,
            self.editSelectedWorksPushButton
        )

    def onDesktopTableViewSelectionChanged(self):
        self.updateSelection(
            self.desktopTableView,
            self.selectedDesktopCountLabel,
            self.desktopTableModel,
            self.completeSelectedDesktopPushButton,
            None  # Assuming there's no edit button for desktop items
        )

    def onCompleteSelectedWorksPushButtonClicked(self):
        with Session(ENGINE) as session:
            for index in self.desktopTableView.selectionModel().selectedRows():
                item: WorkRequest = self.desktopTableModel._data[index.row()]
                workRequest: WorkRequest = session.get(WorkRequest, item.id)
                workRequest.status = WorkRequest.Status.COMPLETED
                session.add(workRequest)
                self.desktopTableModel.removeRow(index.row(), delete=False)
            session.commit()
        self.refreshTableViews()
        
    def onCreateClicked(self, dlg):
        dlg.exec()
        self.refreshTableViews()
        
    def onDeleteRowsClicked(self, tableView: QTableView):
        if self.showConfirmationWarning() != QMessageBox.StandardButton.Ok:
            return

        for index in tableView.selectionModel().selectedRows():
            tableView.model().removeRow(index.row())

    def showConfirmationWarning(self):
        return QMessageBox.warning(
            self.parent(),
            "Удаление объектов",
            "Вы действительно хотите удалить выбранные объекты?",
            defaultButton=QMessageBox.StandardButton.Cancel,
        )


__all__ = ["MainWindow"]
