from PyQt6 import uic
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QDialog, QMessageBox, QComboBox
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import Area, EventType, Event, AssignmentType, Place, Scope, Assignment
from app.ui.dialogs.alerts import validationError
from app.ui.models import TypeListModel
from app.ui.wizards.reservation import ReservationWizard


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

    def onAddButtonClicked(self, **kwargs) -> None:
        self.listViewModel.insertRow(-1, **kwargs)
        index = self.listViewModel.index(self.listViewModel.rowCount() - 1, 0)
        self.listView.edit(index)

    def onDelButtonClicked(self) -> None:
        currentRowIndex = self.listView.currentIndex().row()
        self.listViewModel.removeRow(currentRowIndex)


class AreaMangerDialog(TypeManagerDialog):
    def __init__(self) -> None:
        super().__init__(Area, "Части")
        self.combobox = QComboBox()
        self.combobox.currentTextChanged.connect(self.updateModel)

        with Session(ENGINE) as session:
            self.names = session.exec(select(Place.name)).all()

        self.combobox.addItems(name for name in self.names)
        self.verticalLayout_4.addWidget(self.combobox)

    def exec(self) -> int:
        if not self.names:
            QMessageBox.critical(self, "Ошибка", "Вы должны создать хотя бы одно помещение!")
            return 0
        
        return super().exec()
        
    def updateModel(self, place_name: str):
        with Session(ENGINE) as session:
            self.selected_place = session.exec(select(Place).where(Place.name == place_name)).first()
            areas = session.exec(select(Area).where(Area.place == self.selected_place)).all()

        self.listViewModel = TypeListModel[Area](areas, self)
        self.listView.setModel(self.listViewModel)

        self.delButton.setDisabled(True)
        self.listView.selectionModel().selectionChanged.connect(
            lambda: self.delButton.setDisabled(False)
        )
        
    def onAddButtonClicked(self) -> None:
        super().onAddButtonClicked(place_id=self.selected_place.id)        


class CreateEventDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_event.ui", self)
        
        self.reservationButton.clicked.connect(self.showReservationWizard)

        self.dateDateTimeEdit.setDateTime(QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()
            roomTypeNames = session.exec(select(Place.name)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)
        self.roomComboBox.addItems(eventTypeName for eventTypeName in roomTypeNames)
        
    def showReservationWizard(self):
        event = self.create(True)
        
        wizard = ReservationWizard(event)
        
        if wizard.exec():
            self.reservation = wizard.reservation
        
    def validate(self) -> bool:
        title = self.titleLineEdit.text()

        if not title:
            validationError(self, "Название мероприятия должно быть заполнено!")
            return False
        return True
    
    def create(self, flush=False) -> Event:
        title = self.titleLineEdit.text()
        date = self.dateDateTimeEdit.dateTime().toPyDateTime()
        description = self.descriptionTextEdit.toPlainText()
        event_type_name = self.typeComboBox.currentText()
        room_type_name = self.roomComboBox.currentText()

        if self.entertainemtRadioButton.isChecked():
            section_id = 0
        elif self.enlightenmentRadioButton.isChecked():
            section_id = 1
        else:
            validationError(self, "Создание мероприятий в этом пространстве временно недоступно")
            return

        with Session(ENGINE) as session:
            type_id = session.exec(
                select(EventType.id).where(EventType.name == event_type_name)
            ).first()
            room_id = session.exec(
                select(Place.id).where(Place.name == room_type_name)
            ).first()
            event = Event(
                title=title,
                start_at=date,
                description=description,
                type_id=type_id,
                room_id=room_id,
                scope=section_id + 1,
            )
            session.add(event)
            if flush:
                session.flush()
            else:
                session.add(self.reservation)
                session.commit()
                session.refresh(event)
                session.refresh(self.reservation)
        return event

    def accept(self) -> None:
        if not self.validate():
            return
        
        self.create()
        return super().accept()


class EditEventDialog(QDialog):    
    def __init__(self, event: Event):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_event.ui", self)
        self.setWindowTitle("Редактирование мероприятия")

        self._event = event
        self.titleLineEdit.setText(self._event.title)
        self.descriptionTextEdit.setPlainText(self._event.description)
        self.dateDateTimeEdit.setDateTime(QDateTime(self._event.start_at))

        if event.scope == Scope(2):
            self.enlightenmentRadioButton.setChecked(True)
        if event.scope == Scope(3):
            self.educationRadioButton.setChecked(True)

        # self.formHelpText.setText("Вы редактируете мероприятие в текущем пространстве.")

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()
            roomTypeNames = session.exec(select(Place.name)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in eventTypeNames)
        self.roomComboBox.addItems(eventTypeName for eventTypeName in roomTypeNames)

        with Session(ENGINE) as session:
            eventType = session.get(EventType, self._event.type_id)
            roomType = session.get(Place, self._event.type_id)
            if eventType:
                self.typeComboBox.setCurrentIndex(eventTypeNames.index(eventType.name))
            if roomType:
                self.roomComboBox.setCurrentIndex(roomTypeNames.index(roomType.name))

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
        room_type_name = self.roomComboBox.currentText()


        if self.entertainemtRadioButton.isChecked():
            section_id = 0
        elif self.enlightenmentRadioButton.isChecked():
            section_id = 1
        else:
            QMessageBox.warning(
                self, "Ошибка валидации", "Создание мероприятий в этом пространстве временно недоступно"
            )
            return

        with Session(ENGINE) as session:
            type_id = session.exec(
                select(EventType.id).where(EventType.name == event_type_name)
            ).first()
            room_id = session.exec(
                select(Place.id).where(Place.name == room_type_name)
            ).first()
            self._event.title = title
            self._event.start_at = date
            self._event.description = description
            self._event.type_id = type_id
            self._event.room_id = room_id
            self._event.scope = Scope(section_id + 1)

            session.add(self._event)
            session.commit()
            session.refresh(self._event)

        return super().accept()


class CreateWorkDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_work.ui", self)
        self.dateDateTimeEdit.setDateTime(QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            workTypeNames = session.exec(select(AssignmentType.name)).all()
            roomTypeNames = session.exec(select(Place.name)).all()
            eventNames = session.exec(select(Event.title)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in workTypeNames)
        self.roomComboBox.addItems(eventTypeName for eventTypeName in roomTypeNames)
        self.eventComboBox.addItems(eventTypeName for eventTypeName in eventNames)

    def accept(self) -> None:
        date = self.dateDateTimeEdit.dateTime().toPyDateTime()
        description = self.descriptionTextEdit.toPlainText()
        work_type_name = self.typeComboBox.currentText()
        room = self.roomComboBox.currentText()
        event = self.eventComboBox.currentText()

        if self.draftRadioButton.isChecked():
            status = 1
        elif self.activeRadioButton.isChecked():
            status = 2
        else:
            status = 3

        with Session(ENGINE) as session:
            event_id = session.exec(select(Event.id).where(Event.title == event)).first()
            type_id = session.exec(select(AssignmentType.id).where(AssignmentType.name == work_type_name)).first()
            room_id = session.exec(select(Place.id).where(Place.name == room)).first()

            newWork = Assignment(
                description=description,
                event_id=event_id,
                type_id=type_id,
                room_id=room_id,
                deadline=date,
                state=status,
            )
            session.add(newWork)
            session.commit()

        return super().accept()


class EditWorksDialog(QDialog):
    def __init__(self, work: Assignment):
        super().__init__()
        uic.loadUi("app/ui/dialogs/create_work.ui", self)
        self.setWindowTitle("Редактирование заявки")

        self._work = work
        with Session(ENGINE) as session:
            workTypeNames = session.exec(select(AssignmentType.name)).all()
            roomTypeNames = session.exec(select(Place.name)).all()
            eventNames = session.exec(select(Event.title)).all()
            workType = session.get(AssignmentType, self._work.type_id)
            eventType = session.get(Event, self._work.event_id)
            roomType = session.get(Place, self._work.room_id)

        self.typeComboBox.addItems(eventTypeName for eventTypeName in workTypeNames)
        self.roomComboBox.addItems(eventTypeName for eventTypeName in roomTypeNames)
        self.eventComboBox.addItems(eventTypeName for eventTypeName in eventNames)

        if workType:
            self.typeComboBox.setCurrentIndex(workTypeNames.index(workType.name))
        if eventType:
            self.eventComboBox.setCurrentIndex(eventNames.index(eventType.title))
        if roomType:
            self.roomComboBox.setCurrentIndex(roomTypeNames.index(roomType.name))

        self.descriptionTextEdit.setPlainText(self._work.description)
        self.dateDateTimeEdit.setDateTime(QDateTime(self._work.deadline))

        if self._work.state == Assignment.State(1):
            self.draftRadioButton.setChecked(True)
        if self._work.state == Assignment.State(2):
            self.activeRadioButton.setChecked(True)
        if self._work.state == Assignment.State(3):
            self.completedRadioButton.setChecked(True)

    def accept(self) -> None:
        deadline = self.dateDateTimeEdit.dateTime().toPyDateTime()
        description = self.descriptionTextEdit.toPlainText()
        work_type_name = self.typeComboBox.currentText()
        room = self.roomComboBox.currentText()
        event = self.eventComboBox.currentText()

        if self.draftRadioButton.isChecked():
            status = 1
        elif self.activeRadioButton.isChecked():
            status = 2
        else:
            status = 3

        with Session(ENGINE) as session:
            event_id = session.exec(select(Event.id).where(Event.title == event)).first()
            type_id = session.exec(select(AssignmentType.id).where(AssignmentType.name == work_type_name)).first()
            room_id = session.exec(select(Place.id).where(Place.name == room)).first()

            self._work.description = description
            self._work.state = Assignment.State(status)
            self._work.event_id = event_id
            self._work.type_id = type_id
            self._work.room_id = room_id
            self._work.deadline = deadline

            session.add(self._work)
            session.commit()
            session.refresh(self._work)

        return super().accept()



__all__ = ["TypeManagerDialog", "CreateEventDialog", "EditEventDialog", "CreateWorkDialog"]
