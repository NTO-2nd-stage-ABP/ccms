from PyQt6 import uic
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
from PyQt6.QtWidgets import QMainWindow
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import Event, EventType
from app.ui.dialogs import TypeManagerDialog, CreateActionDialog


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
        self.create_tables()
        self.statusbar.showMessage("Выберите элемент")
        self.create_action.triggered.connect(self.onCreateActionTriggered)
        self.events_type_manager_action.triggered.connect(self.onEventsTypeManagerActionTriggered)

    def create_tables(self):
        self.create_table_ENTERTAINMENT()
        self.create_table_ENLIGHTENMENT()


    def create_table_ENTERTAINMENT(self):
        with Session(ENGINE) as session:
            events = session.exec(select(Event).where(Event.section == 'ENTERTAINMENT')).all()
        model = QStandardItemModel(len(events), 5)
        model.setHorizontalHeaderLabels(["id", 'Название', "Дата", "Описание", "Тип мероприятия"])

        for row in range(len(events)):
            model.setItem(row, 0, QStandardItem(str(events[row].id)))
            model.setItem(row, 1, QStandardItem(events[row].name))
            model.setItem(row, 2, QStandardItem(events[row].date.strftime("%B %d, %Y. %H:%M")))
            model.setItem(row, 3, QStandardItem(events[row].description))
            with Session(ENGINE) as session:
                type = session.exec(select(EventType.name).where(EventType.id == events[row].type_id)).first()
            model.setItem(row, 4, QStandardItem(type))

        self.entertainmentView.setModel(model)


    def create_table_ENLIGHTENMENT(self):
        with Session(ENGINE) as session:
            events = session.exec(select(Event).where(Event.section == 'ENLIGHTENMENT')).all()
        model = QStandardItemModel(len(events), 5)
        model.setHorizontalHeaderLabels(["id", 'Название', "Дата", "Описание", "Тип мероприятия"])

        for row in range(len(events)):
            model.setItem(row, 0, QStandardItem(str(events[row].id)))
            model.setItem(row, 1, QStandardItem(events[row].name))
            model.setItem(row, 2, QStandardItem(events[row].date.strftime("%B %d, %Y. %H:%M")))
            model.setItem(row, 3, QStandardItem(events[row].description))
            with Session(ENGINE) as session:
                type = session.exec(select(EventType.name).where(EventType.id == events[row].type_id)).first()
            model.setItem(row, 4, QStandardItem(type))

        self.enlightenmentView.setModel(model)

    def onEventsTypeManagerActionTriggered(self):
            dlg = TypeManagerDialog()
            dlg.exec()

    def onCreateActionTriggered(self):
        dlg = CreateActionDialog(self.tabWidget.currentIndex())
        dlg.exec()
        self.create_tables()
