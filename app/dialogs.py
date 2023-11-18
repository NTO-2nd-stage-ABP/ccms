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

        self.eventTypeIds = {}
        self.model = QStandardItemModel()
        self.listView.setModel(self.model)

        with Session(ENGINE) as session:
            eventTypes = session.exec(select(EventType)).all()

        for eventType in eventTypes:
            self.eventTypeIds[self.model.rowCount()] = eventType.id
            self.addEventTypeToListView(eventType)

        self.model.dataChanged.connect(self.onDataChanged)
        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)

    def onAddButtonClicked(self):
        with Session(ENGINE) as session:
            latestEventType = session.exec(
                select(EventType).order_by(EventType.id.desc()).limit(1)
            ).first()
            newEventType = EventType(name=f"Вид {1 if latestEventType == None else latestEventType.id + 1}")
            self.addEventTypeToListView(newEventType)
            session.add(newEventType)
            session.commit()
            self.eventTypeIds[self.model.rowCount() - 1] = newEventType.id

    def onDelButtonClicked(self):
        currentRowIndex = self.listView.currentIndex().row()
        
        with Session(ENGINE) as session:
            print(self.eventTypeIds.keys())
            print("pk", self.eventTypeIds[currentRowIndex])
            eventType = session.get(EventType, self.eventTypeIds[currentRowIndex])
            session.delete(eventType)
            session.commit()

        self.model.removeRow(currentRowIndex)
        print(self.eventTypeIds.keys())
        self.eventTypeIds.pop(currentRowIndex)
        print(self.eventTypeIds.keys())
        values = self.eventTypeIds.values()
        self.eventTypeIds = {}
        for i, value in enumerate(values):
            print(i)
            self.eventTypeIds[i] = value
        print(self.eventTypeIds.keys())

    def onDataChanged(self, index):
        with Session(ENGINE) as session:
            print(self.eventTypeIds.keys())
            newName = index.data(Qt.ItemDataRole.DisplayRole)
            eventType = session.get(EventType, self.eventTypeIds[index.row()])

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
