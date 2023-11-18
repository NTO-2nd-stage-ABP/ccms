from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QDialog, QMessageBox

from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import EventType


class TypeManagerDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/events_type_manager.ui", self)

        self.model = QStandardItemModel()
        self.eventTypeIds = dict()
        self.refreshEventTypes()

        self.model.dataChanged.connect(self.onDataChanged)
        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)

    def refreshEventTypes(self):
        self.listView.setModel(self.model)

        with Session(ENGINE) as session:
            eventTypes = session.exec(select(EventType)).all()

        for eventType in eventTypes:
            self.addEventTypeToListView(eventType)

    def onAddButtonClicked(self):
        with Session(ENGINE) as session:
            latestEventType = (
                session.query(EventType)
                .order_by(EventType.id.desc())
                .limit(1)
                .one_or_none()
            )
            newEventType = EventType(
                name=f"Вид {latestEventType.id + 1 if latestEventType else 1}"
            )
            session.add(newEventType)
            session.commit()
            self.addEventTypeToListView(newEventType)

    def onDelButtonClicked(self):
        currentRowIndex = self.listView.currentIndex().row()

        with Session(ENGINE) as session:
            eventType = session.get(EventType, self.eventTypeIds[currentRowIndex])
            session.delete(eventType)
            session.commit()

        self.model.removeRow(currentRowIndex)

        del self.eventTypeIds[currentRowIndex]
        self.eventTypeIds.update(
            {i: value for i, value in enumerate(self.eventTypeIds.values())}
        )

    def onDataChanged(self, index):
        with Session(ENGINE) as session:
            name = index.data(Qt.ItemDataRole.DisplayRole)
            eventType = session.get(EventType, self.eventTypeIds[index.row()])

            if session.query(select(EventType).filter_by(name=name).exists()).scalar():
                self.showUniqueNameWarning()
                self.setModelData(index, eventType.name, Qt.ItemDataRole.DisplayRole)
                return

            eventType.name = name
            session.add(eventType)
            session.commit()

    def setModelData(self, index, value, role):
        self.model.blockSignals(True)
        self.model.setData(index, value, role)
        self.model.blockSignals(False)

    def showUniqueNameWarning(self):
        QMessageBox.warning(self, "Предупреждение", "Такой вид уже существует!")

    def addEventTypeToListView(self, eventType: EventType):
        item = QStandardItem(eventType.name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.eventTypeIds[self.model.rowCount()] = eventType.id
        self.model.appendRow(item)


class CreateActionDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/event_edit.ui", self)
