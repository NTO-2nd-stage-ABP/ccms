from PyQt6 import uic
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QDialog, QMessageBox
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import EventType, Event
from app.ui.event_edit import UiDialogAddEvent
from app.utils.views import GenericListModel


class GenericSequenceManagerDialog(QDialog):
    def __init__(self, _type, header) -> None:
        super().__init__()
        uic.loadUi("app/ui/dialogs/events_type_manager.ui", self)
        
        with Session(ENGINE) as session:
            data = session.exec(select(_type)).all()

        self.label_2.setText(header)
        self.listViewModel = GenericListModel[_type](data, self)
        self.listView.setModel(self.listViewModel)

        self.delButton.setDisabled(True)
        self.listView.selectionModel().selectionChanged.connect(lambda: self.delButton.setDisabled(False))

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


class EditActionDialog(QDialog, UiDialogAddEvent):
    def __init__(self, section_id):
        super().__init__()
        # uic.loadUi("app/ui/dialogs/event_edit.ui", self)
        self.setupUi(self)

        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.comboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)
        self.section_id = section_id

    def accept(self) -> None:
        title = self.lineEdit.text()

        if not title:
            QMessageBox.warning(
                self, "Ошибка проверки", "Название мероприятия должно быть заполнено!"
            )
            return

        date = self.dateTimeEdit.dateTime().toPyDateTime()
        description = self.textEdit.toPlainText()
        event_type_name = self.comboBox.currentText()

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


class EditEventActionDialog(QDialog, UiDialogAddEvent):
    def __init__(self, event: Event):
        super().__init__()
        # uic.loadUi("app/ui/dialogs/event_edit.ui", self)
        self.setupUi(self)
        self.setWindowTitle("Редактирование мероприятия")

        self.__event = event
        self.lineEdit.setText(self.__event.name)
        self.textEdit.setPlainText(self.__event.description)
        self.dateTimeEdit.setDateTime(QDateTime(self.__event.date))
        self.label_5.setText("Вы редактируете мероприятие в текущем пространстве.")

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.comboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)
        
        with Session(ENGINE) as session:
            eventType = session.get(EventType, self.__event.type_id)
            self.comboBox.setCurrentIndex(eventTypeNames.index(eventType.name))

    def accept(self) -> None:
        title = self.lineEdit.text()

        if not title:
            QMessageBox.warning(
                self, "Ошибка проверки", "Название мероприятия должно быть заполнено!"
            )
            return

        date = self.dateTimeEdit.dateTime().toPyDateTime()
        description = self.textEdit.toPlainText()
        event_type_name = self.comboBox.currentText()

        with Session(ENGINE) as session:
            type_id = session.exec(
                select(EventType.id).where(EventType.name == event_type_name)
            ).first()
            self.__event.name = title
            self.__event.date = date
            self.__event.description = description
            self.__event.type_id = type_id

            session.add(self.__event)
            session.commit()
            session.refresh(self.__event)

        return super().accept()
