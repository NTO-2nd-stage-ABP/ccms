from typing import Set
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QWidget, QTableView

from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import (
    Event,
    EventType,
    Place,
    Assignment,
    AssignmentType,
    Reservation,
    Scope
)
from app.ui.dialogs import (
    TypeManagerDialog,
    EventCreateDialog,
    EventUpdateDialog,
    AssignmentCreateDialog,
)
from app.ui.dialogs.ext import AreaMangerDialog, AssignmentUpdateDialog
from app.ui.models import SECTIONS, EventTableModel, AssignmentTableModel, ReservaionTableModel


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
        self.reservationsTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.refreshTableViews()
        
        self.eventsTypeMaximizePushButton.clicked.connect(lambda: self.showTypeManagerDialog(EventType, "Виды мероприятий:"))
        self.worksTypeMaximizePushButton.clicked.connect(lambda: self.showTypeManagerDialog(AssignmentType, "Виды работ:"))
        self.locationsShowButton.clicked.connect(lambda: self.showTypeManagerDialog(Place, "Помещения:"))
        self.areasOpenButton.clicked.connect(self.showAreasManager)

        self.newEventPushButton.clicked.connect(lambda: self.onCreateClicked(EventCreateDialog()))
        self.newWorkPushButton.clicked.connect(lambda: self.onCreateClicked(AssignmentCreateDialog()))
        
        self.editSelectedEventsPushButton.clicked.connect(self.onEditSelectedEventsPushButtonClicked)
        self.editSelectedWorksPushButton.clicked.connect(self.onEditSelectedWorksPushButtonClicked)
        
        self.deleteSelectedEventsPushButton.clicked.connect(lambda: self.onDeleteRowsClicked(self.eventsTableView))
        self.deleteSelectedWorksPushButton.clicked.connect(lambda: self.onDeleteRowsClicked(self.worksTableView))
        self.deleteSelectedReservationsPushButton.clicked.connect(lambda: self.onDeleteRowsClicked(self.reservationsTableView))

        self.completeSelectedDesktopPushButton.clicked.connect(self.onCompleteSelectedWorksPushButtonClicked)

        with Session(ENGINE) as session:
            workTypeNames = session.exec(select(AssignmentType.name)).all()

        self.comboBox_12.addItems(workTypeName for workTypeName in workTypeNames)
        self.pushButton_2.clicked.connect(self.filterByWorkTypeName)
        self.resetDesktopFilterButton.clicked.connect(self.resetDesktopFilter)
        
        self.comboBox.addItems(section for section in SECTIONS.values())
        self.pushButton_3.clicked.connect(self.filterByWorkSection)
        self.pushButton_4.clicked.connect(self.resetEventsFilter)
        
    def showAreasManager(self):
        AreaMangerDialog().exec()
        self.refreshTableViews()

    def showTypeManagerDialog(self, _type, title):
        TypeManagerDialog(_type, title).exec()
        self.refreshTableViews()
    
    events_filter = None
    work_requests_filter = None
        
    def resetDesktopFilter(self):
        self.work_requests_filter = None
        self.comboBox_12.blockSignals(True)
        self.comboBox_12.setCurrentIndex(0)
        self.comboBox_12.blockSignals(False)
        self.refreshDesktop()
        
    def resetEventsFilter(self):
        self.events_filter = None
        self.comboBox.blockSignals(True)
        self.comboBox.setCurrentIndex(0)
        self.comboBox.blockSignals(False)
        self.refreshTableViews()
    
    def filterByWorkSection(self):
        name = self.comboBox.currentText()
        self.events_filter = (Event.scope == Scope(list(SECTIONS.values()).index(name) + 1))
        self.refreshTableViews()

    def filterByWorkTypeName(self):
        name = self.comboBox_12.currentText()
        with Session(ENGINE) as session:
            type_id = session.exec(
                select(AssignmentType.id).where(AssignmentType.name == name)
            ).first()
        self.work_requests_filter = (Assignment.type_id == type_id)
        self.refreshDesktop()

    def refreshDesktop(self):
        with Session(ENGINE) as session:
            statement = select(Assignment).where(Assignment.state == Assignment.State.ACTIVE)
            if self.work_requests_filter is not None:
                statement = statement.where(self.work_requests_filter)
            data: Set[Assignment] = session.exec(statement).all()

        self.desktopTableModel = AssignmentTableModel(data)
        self.desktopTableView.setModel(self.desktopTableModel)
        self.desktopTableView.selectionModel().selectionChanged.connect(
            self.onDesktopTableViewSelectionChanged
        )
        self.completeSelectedDesktopPushButton.setEnabled(False)
        self.onDesktopTableViewSelectionChanged()
        
    # def refreshWorkRequests(self, *args, where=None):

    def refreshTableViews(self, *args):
        self.refreshDesktop()

        with Session(ENGINE) as session:
            statement = select(Event)
            if self.events_filter is not None:
                statement = statement.where(self.events_filter)
            events = session.exec(statement).all()
            workRequests: Set[Assignment] = session.exec(select(Assignment)).all()
            reservations: Set[Reservation] = session.exec(select(Reservation)).all()            
            
            self.worksTableModel = AssignmentTableModel(workRequests)
            self.eventsTableModel = EventTableModel(events)
            self.reservationsTableModel = ReservaionTableModel(reservations)

        self.eventsTableView.setModel(self.eventsTableModel)
        self.worksTableView.setModel(self.worksTableModel)
        self.reservationsTableView.setModel(self.reservationsTableModel)

        self.eventsTableView.selectionModel().selectionChanged.connect(
            self.onEventsTableViewSelectionChanged
        )
        self.worksTableView.selectionModel().selectionChanged.connect(
            self.onWorkTableViewSelectionChanged
        )
        self.reservationsTableView.selectionModel().selectionChanged.connect(
            self.onReservationsTableViewSelectionChanged
        )
        
        self.deleteSelectedEventsPushButton.setEnabled(False)
        self.editSelectedEventsPushButton.setEnabled(False)
        self.editSelectedWorksPushButton.setEnabled(False)
        self.deleteSelectedWorksPushButton.setEnabled(False)
        self.deleteSelectedReservationsPushButton.setEnabled(False)
        self.onWorkTableViewSelectionChanged()
        self.onEventsTableViewSelectionChanged()
        self.onReservationsTableViewSelectionChanged()

    def onEditSelectedEventsPushButtonClicked(self):
        index = self.eventsTableView.selectedIndexes()[0].row()
        dlg = EventUpdateDialog(self.eventsTableModel._data[index])
        dlg.exec()

    def onEditSelectedWorksPushButtonClicked(self):
        index = self.worksTableView.selectedIndexes()[0].row()
        dlg = AssignmentUpdateDialog(self.worksTableModel._data[index])
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
        
    def onReservationsTableViewSelectionChanged(self):
        self.updateSelection(
            self.reservationsTableView,
            self.selectedReservationsCountLabel,
            self.reservationsTableModel,
            self.deleteSelectedReservationsPushButton,
            None  # Assuming there's no edit button for reservation items
        )

    def onCompleteSelectedWorksPushButtonClicked(self):
        with Session(ENGINE) as session:
            for index in self.desktopTableView.selectionModel().selectedRows():
                item: Assignment = self.desktopTableModel._data[index.row()]
                workRequest: Assignment = session.get(Assignment, item.id)
                workRequest.state = Assignment.State.COMPLETED
                session.add(workRequest)
                self.desktopTableModel.removeRow(index.row(), delete=False)
            session.commit()
        self.refreshTableViews()
        
    def onCreateClicked(self, dlg):
        dlg.exec()
        self.refreshTableViews()
        
    def onDeleteRowsClicked(self, tableView: QTableView):
        if self.showConfirmationWarning() == QMessageBox.StandardButton.No:
            return

        for index in tableView.selectionModel().selectedRows():
            tableView.model().removeRow(index.row())
            
        self.refreshTableViews()

    def showConfirmationWarning(self):
        return QMessageBox.question(
            self.parent(),
            "Удаление объектов",
            "Вы действительно хотите удалить выбранные объекты?",
        )


__all__ = ["MainWindow"]
