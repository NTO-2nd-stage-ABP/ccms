from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow

from app.ui.table import AssignmentTable, EducationTable, EventTable, ReservationTable, DesktopTable
from app.ui.widgets import WidgetMixin


class MainWindow(QMainWindow, WidgetMixin):
    """
    Represents the Main-Window of this application.
    """
    
    ui_path = "app/ui/main_window.ui"

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

        self.desktopLayout.addWidget(self.desktop)
        self.assignmentsLayout.addWidget(self.assignments)
        self.eventsLayout.addWidget(self.events)
        self.educationLayout.addWidget(self.clubs)
        self.locationsLayout.addWidget(self.reservations)

        self.tabWidget.currentChanged.connect(self.refresh_current_tab)
        self.refresh_current_tab(self.tabWidget.currentIndex())

    @pyqtSlot(int)
    def refresh_current_tab(self, index: int) -> None:
        self.views[index].refresh()


__all__ = ["MainWindow"]
