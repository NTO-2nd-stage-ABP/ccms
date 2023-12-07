from typing import Dict, Final
from datetime import time
from sqlmodel import Session, select

from PyQt6 import QtGui, uic, QtWidgets, QtCore

from app.db import ENGINE
from app.db.models import (
    Area,
    BaseModel,
    Club,
    DaySchedule,
    ClubType,
    EventType,
    Event,
    AssignmentType,
    Location,
    Reservation,
    Scope,
    Assignment,
    Teacher,
    Weekday,
)
from app.ui.widgets import WidgetMixin
from app.ui.models import TypeListModel
from app.ui.dialogs.alerts import validationError
from app.ui.wizards.reservation import ReservationWizard

from datetime import datetime

from PyQt6 import QtCore, QtWidgets

DATE_FORMAT = "%d-%b-%y"


class DateDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        widget = QtWidgets.QDateEdit(parent)
        widget.setCalendarPopup(True)
        return widget

    def setEditorData(self, editor, index):
        if isinstance(editor, QtWidgets.QDateEdit):
            dt_str = index.data(QtCore.Qt.ItemDataRole.EditRole)
            dt = datetime.strptime(dt_str, DATE_FORMAT)
            editor.setDate(dt)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtWidgets.QDateEdit):
            dt = editor.date().toPyDate()
            model.setData(index, dt, QtCore.Qt.ItemDataRole.EditRole)
            return
        super().setModelData(editor, model, index)
        

class TypeManagerDialog(QtWidgets.QDialog):
    def __init__(self, _type, parent) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/dialogs/type_manager.ui", self)

        with Session(ENGINE) as session:
            data = session.exec(select(_type)).all()

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
        self.listView.setCurrentIndex(index)

    def onDelButtonClicked(self) -> None:
        currentRowIndex = self.listView.currentIndex().row()
        self.listViewModel.removeRow(currentRowIndex)


class AreaManagerDialog(TypeManagerDialog):
    def __init__(self, parent) -> None:
        super().__init__(Area, parent)
        self.combobox = QtWidgets.QComboBox()
        self.combobox.currentTextChanged.connect(self.updateModel)

        with Session(ENGINE) as session:
            self.names = session.exec(select(Location.name)).all()

        self.combobox.addItems(name for name in self.names)
        self.verticalLayout_4.addWidget(self.combobox)

    def exec(self) -> int:
        if self.names:
            return super().exec()
        validationError(self, "Вы должны создать хотя бы одно помещение!")
        return False

    def updateModel(self, name: str):
        with Session(ENGINE) as session:
            self.location = session.exec(select(Location).where(Location.name == name)).first()
            self.listViewModel = TypeListModel[Area](self.location.areas, self)

        self.listView.setModel(self.listViewModel)

        self.delButton.setDisabled(True)
        self.listView.selectionModel().selectionChanged.connect(
            lambda: self.delButton.setDisabled(not(bool(self.listView.selectedIndexes())))
        )

    def onAddButtonClicked(self) -> None:
        super().onAddButtonClicked(location_id=self.location.id)


class DialogView(QtWidgets.QDialog, WidgetMixin):
    model: BaseModel

    def __init__(self, obj=None, parent: QtWidgets.QWidget | None = None) -> None:
        self.obj = obj
        super().__init__(parent)

    @property
    def obj(self):
        return self._obj or self.model()

    @obj.setter
    def obj(self, value) -> None:
        self._obj = value


class EventCreateDialog(DialogView):
    model = Event
    ui_path = "app/ui/dialogs/create_event.ui"

    @property
    def scope_radios(self) -> Dict[Scope, QtWidgets.QRadioButton]:
        return {
            Scope.ENTERTAINMENT: self.entertainmentRadioButton,
            Scope.ENLIGHTENMENT: self.enlightenmentRadioButton,
            Scope.EDUCATION: self.educationRadioButton,
        }

    def setup_ui(self) -> None:
        self.reservationButton.clicked.connect(self.showReservationWizard)

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.typeComboBox.addItems(eventTypeNames)
        self.dateDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())

    def create(self, commit=True) -> Event:
        with Session(ENGINE) as session:
            event = self.obj

            event.title = self.titleLineEdit.text()
            event.start_at = self.dateDateTimeEdit.dateTime().toPyDateTime()
            event.description = self.descriptionTextEdit.toPlainText()
            event.type_id = session.exec(select(EventType.id).where(EventType.name == self.typeComboBox.currentText())).first()
            event.scope = next(scope for scope, radio in self.scope_radios.items() if radio.isChecked())
            
            session.add(event)
            if commit:
                if hasattr(self, "reservation"):
                    session.add(self.reservation)
                session.commit()
            else:
                session.flush()
        return event
                
    def showReservationWizard(self):
        event = self.create(False)

        wizard = ReservationWizard(event, self)

        if not wizard.exec():
            return

        with Session(ENGINE) as session:
            location = session.get(Location, wizard.reservation.location_id)
            self.reservation = wizard.reservation
            self.locationLabel.setText(location.name)
            self.areasLabel.setEnabled(any(wizard.reservation.areas))
            self.areasListWidget.clear()
            self.areasListWidget.addItems(area.name for area in wizard.reservation.areas)

    def accept(self) -> None:
        if not self.titleLineEdit.text():
            validationError(self, "Название мероприятия должно быть заполнено!")
            return

        self.create()
        return super().accept()


class EventUpdateDialog(EventCreateDialog):
    title = "Редактирование мероприятия"

    def setup_ui(self) -> None:
        super().setup_ui()

        with Session(ENGINE) as session:
            session.add(self.obj)
            
            if any(self.obj.reservations):
                self.groupBox.setEnabled(False)
                reservation = session.exec(select(Reservation).where(Reservation.event_id == self.obj.id)).first()
                self.locationLabel.setText(reservation.location.name)
                self.areasListWidget.addItems(area.name for area in reservation.areas)

        self.titleLineEdit.setText(self.obj.title)
        self.descriptionTextEdit.setPlainText(self.obj.description)
        self.dateDateTimeEdit.setDateTime(QtCore.QDateTime(self.obj.start_at))
        self.scope_radios[self.obj.scope].setChecked(True)

        if self.obj.type:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(self.obj.type.name))


class AssignmentCreateDialog(DialogView):
    model = Assignment
    ui_path = "app/ui/dialogs/create_work.ui"

    @property
    def state_radios(self) -> Dict[Assignment.State, QtWidgets.QRadioButton]:
        return {
            Assignment.State.DRAFT: self.draftRadioButton,
            Assignment.State.ACTIVE: self.activeRadioButton,
            Assignment.State.COMPLETED: self.completedRadioButton,
        }

    def setup_ui(self):
        self.dateDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            workTypeNames = session.exec(select(AssignmentType.name)).all()
            roomTypeNames = session.exec(select(Location.name)).all()
            eventNames = session.exec(select(Event.title)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in workTypeNames)
        self.roomComboBox.addItems(eventTypeName for eventTypeName in roomTypeNames)
        self.eventComboBox.addItems(eventTypeName for eventTypeName in eventNames)

    def accept(self) -> None:
        with Session(ENGINE) as session:
            assignment: Assignment = self.obj
            assignment.state = next(scope for scope, radio in self.state_radios.items() if radio.isChecked())
            assignment.deadline = self.dateDateTimeEdit.dateTime().toPyDateTime()
            assignment.description = self.descriptionTextEdit.toPlainText()
            assignment.event_id = session.exec(select(Event.id).where(Event.title == self.eventComboBox.currentText())).first()
            assignment.location_id = session.exec(select(Location.id).where(Location.name == self.roomComboBox.currentText())).first()
            assignment.type_id = session.exec(select(AssignmentType.id).where(AssignmentType.name == self.typeComboBox.currentText())).first()

            session.add(assignment)
            session.commit()

        return super().accept()


class AssignmentUpdateDialog(AssignmentCreateDialog):
    title = "Редактирование заявки"

    def setup_ui(self) -> None:
        super().setup_ui()

        self.state_radios[self.obj.state].setChecked(True)
        self.descriptionTextEdit.setPlainText(self.obj.description)
        self.dateDateTimeEdit.setDateTime(QtCore.QDateTime(self.obj.deadline))

        if self.obj.type:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(self.obj.type.name))
        if self.obj.event:
            self.eventComboBox.setCurrentIndex(self.eventComboBox.findText(self.obj.event.title))
        if self.obj.location:
            self.roomComboBox.setCurrentIndex(self.roomComboBox.findText(self.obj.location.name))


WEEKDAY_NAMES = {
   Weekday.MONDAY: "Понедельник",
   Weekday.TUESDAY: "Вторник",
   Weekday.WEDNESDAY: "Среда",
   Weekday.THURSDAY: "Четверг",
   Weekday.FRIDAY: "Пятница",
   Weekday.SATURDAY: "Суббота",
   Weekday.SUNDAY: "Воскресенье",
}

DEFAULT_START_AT_TIME = time(14)
DEFAULT_END_AT_TIME = time(16)


class DayScheduleGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        day: Weekday,
        is_checked: bool = False,
        default_start_at_time: time = DEFAULT_START_AT_TIME,
        default_end_at_time: time = DEFAULT_END_AT_TIME,
        parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(WEEKDAY_NAMES[day], parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setCheckable(True)
        self.setChecked(is_checked)
        
        self.weekday = day
        
        self.start_at_label = QtWidgets.QLabel("От", self)
        self.start_at_time_edit = QtWidgets.QTimeEdit(QtCore.QTime(default_start_at_time), self)
        
        self.end_at_label = QtWidgets.QLabel("до", self)
        self.end_at_time_edit = QtWidgets.QTimeEdit(QtCore.QTime(default_end_at_time), self)
        self.spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        
        self.layout().addWidget(self.start_at_label)
        self.layout().addWidget(self.start_at_time_edit)
        self.layout().addWidget(self.end_at_label)
        self.layout().addWidget(self.end_at_time_edit)
        self.layout().addItem(self.spacer)


COLUMN_COUNT = 2


class DaysScheduleManagerDialog(QtWidgets.QDialog, WidgetMixin):
    ui_path = "app/ui/dialogs/schedule_manager.ui"
    
    def __init__(self, days: list[DaySchedule] = [], parent: QtWidgets.QWidget | None = None) -> None:
        self.days: list[DaySchedule] = days
        super().__init__(parent)
        
    @property
    def weekdays(self):
        return frozenset(schedule_day.weekday for schedule_day in self.days)
    
    @property
    def boxes(self) -> set[DayScheduleGroupBox]:
        return frozenset(self.gridLayout.itemAt(i).widget() for i in range(self.gridLayout.count()))
    
    def setup_ui(self) -> None:
        weekday_days = {
            sd.weekday: DayScheduleGroupBox(sd.weekday, True, sd.start_at, sd.end_at)
            for sd in self.days
        }

        for i, weekday in enumerate(Weekday):
            box = weekday_days.get(weekday, DayScheduleGroupBox(weekday))

            col = i % COLUMN_COUNT
            row = i // COLUMN_COUNT + i - col
            self.gridLayout.addWidget(box, row, col)
            
    def accept(self) -> None:
        for box in self.boxes:
            day_schedule = next((day for day in self.days if day.weekday == box.weekday), DaySchedule())
            if box.isChecked():
                day_schedule.start_at = box.start_at_time_edit.time().toPyTime()
                day_schedule.end_at = box.end_at_time_edit.time().toPyTime()

                if day_schedule.weekday:
                    continue

                day_schedule.weekday = box.weekday
                self.days.append(day_schedule)
            elif day_schedule.id:
                self.days.remove(day_schedule)
            elif day_schedule.weekday:
                self.days = [day for day in self.days if day != day_schedule]

        return super().accept()
    
    def reject(self) -> None:
        for box in self.boxes:
            box.setChecked(box.weekday in self.weekdays)
        return super().reject()


class ClubCreateDialog(DialogView):
    model = Club
    ui_path = "app/ui/dialogs/create_club.ui"

    def setup_ui(self) -> None:
        self.schedule_manager = DaysScheduleManagerDialog(self.obj.days, self)
        self.schedule_manager.accepted.connect(self._update_schedule_type_label)
        self.editScheduleButton.clicked.connect(self.schedule_manager.exec)

        self.startDateEdit.setMinimumDate(QtCore.QDate.currentDate())

        with Session(ENGINE) as session:
            self.typeComboBox.addItems(session.exec(select(ClubType.name)).all())
            self.locationComboBox.addItems(session.exec(select(Location.name)).all())
            self.teacherComboBox.addItems(session.exec(select(Teacher.name)).all())

    def accept(self) -> None:
        if not self.titleLineEdit.text():
            validationError(self, "Название не должно быть пустым!")
            return
        if not self.obj.days and not self.schedule_manager.days:
            validationError(self, "Выберите хотя бы один день недели!")
            return

        with Session(ENGINE) as session:
            club: Club = self.obj
            club.title = self.titleLineEdit.text()
            club.start_at = self.startDateEdit.date().toPyDate()
            club.teacher_id = session.exec(select(Teacher.id).where(Teacher.name == self.teacherComboBox.currentText())).first()
            club.location_id = session.exec(select(Location.id).where(Location.name == self.locationComboBox.currentText())).first()
            club.type_id = session.exec(select(ClubType.id).where(ClubType.name == self.typeComboBox.currentText())).first()

            session.add(club)
            session.commit()

        return super().accept()

    def _update_schedule_type_label(self):
        self.scheduleTypeLabel.setText(str(len(self.schedule_manager.days)))


class ClubUpdateDialog(ClubCreateDialog):
    title = "Редактирование секции"
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.scheduleTypeLabel.setText(str(len(self.obj.days)))
    
        self.titleLineEdit.setText(self.obj.title)
        self.startDateEdit.setDate(QtCore.QDate(self.obj.start_at))

        if self.obj.type:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(self.obj.type.name))
        if self.obj.teacher:
            self.teacherComboBox.setCurrentIndex(self.teacherComboBox.findText(self.obj.teacher.name))
        if self.obj.location:
            self.locationComboBox.setCurrentIndex(self.locationComboBox.findText(self.obj.location.name))
    

__all__ = [
    "AreaManagerDialog",
    "TypeManagerDialog",
    "EventCreateDialog",
    "EventUpdateDialog",
    "AssignmentCreateDialog",
    "AssignmentUpdateDialog",
    "ClubCreateDialog",
    "ClubUpdateDialog",
]
