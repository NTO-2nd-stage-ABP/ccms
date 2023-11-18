from PyQt6 import uic
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QDialog, QMessageBox
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
    def __init__(self, section_id):
        super().__init__()
        uic.loadUi("app/ui/dialogs/event_edit.ui", self)
        
        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.comboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)
        self.section_id = section_id
                
    def accept(self) -> None:
        title = self.lineEdit.text()

        if not title:
            QMessageBox.warning(self, "Ошибка валидации.", "Название мероприятия не должно быть пустым.")
            return

        date = self.dateTimeEdit.dateTime().toPyDateTime()
        description = self.textEdit.toPlainText()
        event_type_name = self.comboBox.currentText()

        with Session(ENGINE) as session:
            type_id = session.exec(select(EventType.id).where(EventType.name == event_type_name)).first()
            newEvent = Event(name=title, date=date, description=description, type_id=type_id, section=self.section_id + 1)
            session.add(newEvent)
            session.commit()
            
        return super().accept()
                