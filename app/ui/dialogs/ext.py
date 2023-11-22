from PyQt6 import uic
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QDialog, QMessageBox
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import EventType, Event
from app.ui.models import TypeListModel


class TypeManagerDialog(QDialog):
    def __init__(self, _type, header) -> None:
        super().__init__()
        uic.loadUi("app/ui/dialogs/type_manager.ui", self)

        with Session(ENGINE) as session:
            data = session.exec(select(_type)).all()

        self.label_2.setText(header)
        self.listViewModel = TypeListModel[_type](data, self)
        self.listView.setModel(self.listViewModel)

        self.delButton.setDisabled(True)
        self.listView.selectionModel().selectionChanged.connect(
            lambda: self.delButton.setDisabled(False)
        )

        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)

    def onAddButtonClicked(self) -> None:
        self.listViewModel.insertRow(-1)
        index = self.listViewModel.index(self.listViewModel.rowCount() - 1, 0)

        # Access or modify the data in the index
        # data = index.data()

        self.listView.edit(index)

    def onDelButtonClicked(self) -> None:
        currentRowIndex = self.listView.currentIndex().row()
        self.listViewModel.removeRow(currentRowIndex)


class CreateEventDialog(QDialog):
    def __init__(self, section_id):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_event.ui", self)

        self.dateDateTimeEdit.setDateTime(QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)
        self.section_id = section_id

    def accept(self) -> None:
        title = self.titleLineEdit.text()

        if not title:
            QMessageBox.warning(
                self, "Ошибка проверки", "Название мероприятия должно быть заполнено!"
            )
            return

        date = self.dateDateTimeEdit.dateTime().toPyDateTime()
        description = self.descriptionTextEdit.toPlainText()
        event_type_name = self.typeComboBox.currentText()

        with Session(ENGINE) as session:
            type_id = session.exec(
                select(EventType.id).where(EventType.name == event_type_name)
            ).first()
            newEvent = Event(
                name=title,
                date=date,
                description=description,
                type_id=type_id,
                section=self.section_id + 1,
            )
            session.add(newEvent)
            session.commit()

        return super().accept()


class EditEventDialog(QDialog):    
    def __init__(self, event: Event):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_event.ui", self)
        self.setWindowTitle("Редактирование мероприятия")

        self._event = event
        self.titleLineEdit.setText(self._event.name)
        self.descriptionTextEdit.setPlainText(self._event.description)
        self.dateDateTimeEdit.setDateTime(QDateTime(self._event.date))
        self.formHelpText.setText("Вы редактируете мероприятие в текущем пространстве.")

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)

        with Session(ENGINE) as session:
            eventType = session.get(EventType, self._event.type_id)
            if eventType:
                self.typeComboBox.setCurrentIndex(eventTypeNames.index(eventType.name))

    def accept(self) -> None:
        title = self.titleLineEdit.text()

        if not title:
            QMessageBox.warning(
                self, "Ошибка валидации", "Название мероприятия должно быть заполнено!"
            )
            return

        date = self.dateDateTimeEdit.dateTime().toPyDateTime()
        description = self.descriptionTextEdit.toPlainText()
        event_type_name = self.typeComboBox.currentText()

        with Session(ENGINE) as session:
            type_id = session.exec(
                select(EventType.id).where(EventType.name == event_type_name)
            ).first()
            self._event.name = title
            self._event.date = date
            self._event.description = description
            self._event.type_id = type_id

            session.add(self._event)
            session.commit()
            session.refresh(self._event)

        return super().accept()


class CreateWorkDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_work.ui", self)


__all__ = ["TypeManagerDialog", "CreateEventDialog", "EditEventDialog", "CreateWorkDialog"]
