from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QTableView, QHeaderView
from sqlmodel import Session, select
from app.db import ENGINE
from app.db.models import Club
from app.ui.models.models import ScheduleTableModel
from app.ui.utils import export

from app.ui.widgets.tables.tables import AssignmentTable, EducationTable, EventTable, ReservationTable, DesktopTable
from app.ui.widgets.mixins import WidgetMixin


class MainWindow(QMainWindow, WidgetMixin):
    """
    Represents the Main-Window of this application.
    """
    
    ui_path = "app/ui/assets/windows/main-window.ui"

    def setup_ui(self) -> None:
        self.events = EventTable(self)
        self.assignments = AssignmentTable(self)
        self.reservations = ReservationTable(self)
        self.clubs = EducationTable(self)
        self.desktop = DesktopTable(self)
        
        self.views = [
            self.desktop,
            self.assignments,
            self.events,
            self.clubs,
            self.reservations,
        ]
        
        with Session(ENGINE) as session:
            data = session.exec(select(Club)).all()
        
        self.schedule = QTableView(self)
        self.model = ScheduleTableModel(data)
        self.schedule.setModel(self.model)
        self.schedule.setWordWrap(True)
        self.schedule.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.pushButton.clicked.connect(lambda: export(self.model, self, True))

        self.desktopLayout.addWidget(self.desktop)
        self.assignmentsLayout.addWidget(self.assignments)
        self.eventsLayout.addWidget(self.events)
        self.verticalLayout.addWidget(self.clubs)
        self.verticalLayout_2.addWidget(self.schedule)
        self.locationsLayout.addWidget(self.reservations)

        self.tabWidget.currentChanged.connect(self.refresh_current_tab)
        self.refresh_current_tab(self.tabWidget.currentIndex())

    @pyqtSlot(int)
    def refresh_current_tab(self, index: int) -> None:
        self.views[index].refresh()


__all__ = ["MainWindow"]
