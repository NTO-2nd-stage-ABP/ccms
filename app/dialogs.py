from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import EventType


class TypeManagerDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/events_type_manager.ui", self)

        self.model = QStandardItemModel()
        self.listView.setModel(self.model)

        with Session(ENGINE) as session:
            eventTypes = session.exec(select(EventType)).all()

        for eventType in eventTypes:
            self.addEventTypeToListView(eventType)

        self.model.dataChanged.connect(self.onDataChanged)
        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)

    def onAddButtonClicked(self):
        with Session(ENGINE) as session:
            newEventType = EventType(name=f"Вид {self.model.rowCount() + 1}")
            self.addEventTypeToListView(newEventType)
            session.add(newEventType)
            session.commit()

    def onDelButtonClicked(self):
        with Session(ENGINE) as session:
            currentRowIndex = self.listView.currentIndex().row()
            eventType = session.get(EventType, currentRowIndex + 1)
            session.delete(eventType)
            session.commit()
            self.model.removeRow(currentRowIndex)

    def onDataChanged(self, index):
        with Session(ENGINE) as session:
            newName = index.data(Qt.ItemDataRole.DisplayRole)
            eventType = session.get(EventType, index.row() + 1)

            if session.query(
                select(EventType).where(EventType.name == newName).exists()
            ).scalar():
                QMessageBox.critical(
                    self,
                    "Вид мероприятия с таким названием уже существует!",
                    "Введите другое название.",
                )
                self.model.blockSignals(True)
                self.model.setData(index, eventType.name, Qt.ItemDataRole.DisplayRole)
                self.model.blockSignals(False)
                return

            eventType.name = newName
            session.add(eventType)
            session.commit()

    def addEventTypeToListView(self, eventType: EventType):
        item = QStandardItem(eventType.name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.model.appendRow(item)


class CreateActionDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/event_edit.ui", self)
