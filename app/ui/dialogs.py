from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import EventType, Event
from app.utils.views import EventTypesListModel


class TypeManagerDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("app/ui/dialogs/events_type_manager.ui", self)

        self.listViewModel = EventTypesListModel(self)
        self.listView.setModel(self.listViewModel)

        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)

    def onAddButtonClicked(self) -> None:
        self.listViewModel.insertRow(-1)

    def onDelButtonClicked(self) -> None:
        currentRowIndex = self.listView.currentIndex().row()
        self.listViewModel.removeRow(currentRowIndex)


class CreateActionDialog(QDialog):
    def __init__(self, space):
        super().__init__()
        uic.loadUi("app/ui/dialogs/event_edit.ui", self)

        with Session(ENGINE) as session:
            eventTypes = session.exec(select(EventType)).all()

        self.comboBox.addItems([i.name for i in eventTypes])
        self.space = space
        self.buttonBox.accepted.connect(self.accept)

    def accept(self) -> None:
        title = self.lineEdit.text()
        type = self.comboBox.currentText()
        date = self.dateTimeEdit.dateTime().toPyDateTime()
        description = self.textEdit.toPlainText()

        with Session(ENGINE) as session:
            type_id = session.exec(select(EventType).where(EventType.name == type)).one().id
            newEvent = Event(name=title, date=date, description=description, type_id=type_id, section=self.space + 1)
            session.add(newEvent)
            session.commit()


    # def onAddButtonClicked(self) -> None:
    #     self.listViewModel.insertRow(-1)
