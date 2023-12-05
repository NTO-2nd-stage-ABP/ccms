import csv

from os.path import expanduser

import typing
from sqlmodel import Session, Column, select, delete

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QMessageBox, QFileDialog, QPushButton, QGroupBox, QLabel, QComboBox, QDateTimeEdit
from app.ui.dialogs.alerts import confirm
from app.ui.models import SECTIONS, ClubTableModel, EventTableModel, AssignmentTableModel, ReservaionTableModel

from app.ui.dialogs import (
    TypeManagerDialog,
    EventCreateDialog,
    EventUpdateDialog,
    AssignmentCreateDialog,
    AssignmentUpdateDialog,
    AreaManagerDialog,
    ClubCreateDialog,
    ClubUpdateDialog
)
from app.db import ENGINE
from app.ui.models import BaseTableModel
from app.db.models import (
    Area,
    Club,
    ClubType,
    Event,
    Assignment,
    Location,
    Reservation,
    AssignmentType,
    BaseModel,
    EventType,
    Teacher
)
from app.ui.widgets import WidgetMixin


class FilterBox(QGroupBox, WidgetMixin):
    ui_path = "app/ui/filter.ui"
    title = None
    
    def __init__(self, filters, parent: "Table") -> None:
        self._filters = filters
        self._applies = []
        super().__init__(parent)

    def setup_ui(self) -> None:
        self.resetButton.clicked.connect(self.reset)
        self.applyButton.clicked.connect(self.apply)
        
        for text, (expr, _type) in self._filters.items():
            if _type == QComboBox:
                with Session(ENGINE) as session:
                    data = session.exec(select(expr)).all()
                    combo = QComboBox(self)
                    combo.setPlaceholderText("Не выбрано")
                    combo.addItems(data)
                    self._applies.append((combo, (expr, _type)))
                    self.formLayout.addRow(QLabel(text, self), combo)
            elif _type == QDateTimeEdit:                
                self.formLayout.addRow(QLabel(text, self))
                fr = QDateTimeEdit(self)
                fr.setCalendarPopup(True)
                fr.setDate(fr.minimumDate())
                to = QDateTimeEdit(self)
                to.setCalendarPopup(True)
                to.setDate(to.minimumDate())
                self._applies.append(((fr, to), (expr, _type)))
                self.formLayout.addRow(QLabel("От:", self), fr)
                self.formLayout.addRow(QLabel("До:", self), to)
           
    def reset(self):
        self.parent().wheres = []
        for field, (_, _type) in self._applies:
            if _type == QComboBox:
                field.setCurrentIndex(-1)
            if _type == QDateTimeEdit:
                fr, to = field
                fr.setDateTime(fr.minimumDateTime())
                to.setDateTime(to.minimumDateTime())
        self.parent().refresh(filter=False)
    
    def apply(self):
        self.parent().wheres = []
        for field, (expr, _type) in self._applies:
            if _type == QComboBox:
                value = field.currentText()
                if value:
                    self.parent().wheres.append(expr == value)
            if _type == QDateTimeEdit:
                fr, to = field
                fr_dt = fr.dateTime().toPyDateTime()
                to_dt = to.dateTime().toPyDateTime()
                if fr_dt != fr.minimumDateTime().toPyDateTime():
                    self.parent().wheres.append(fr_dt < expr)
                if to_dt != to.minimumDateTime().toPyDateTime():
                    self.parent().wheres.append(expr < to_dt)
        self.parent().refresh(filter=False)


class Table(QWidget, WidgetMixin):
    ui_path = "app/ui/table.ui"

    table: BaseModel
    table_model: BaseTableModel
    create_dialog: QDialog | None = None
    update_dialog: QDialog | None = None
    delete_visible: bool = True
    filter: Column = None
    filters: typing.Dict[str, Column] = None
    joins = None
    wheres = []
    
    @property
    def selected_indexes(self):
        return sorted(i.row() for i in self.tableView.selectionModel().selectedRows())
    
    def __init__(self, parent: QWidget | None = None) -> None:
        self._extra_buttons = []
        super().__init__(parent)
        
    def setup_ui(self) -> None:
        if self.create_dialog:
            self.createButton.clicked.connect(self.create)
        else:
            self.createButton.setVisible(False)

        if self.update_dialog:
            self.updateButton.clicked.connect(self.update)
        else:
            self.updateButton.setVisible(False)
            
        if self.delete_visible:
            self.deleteButton.clicked.connect(self.delete)
        else:
            self.deleteButton.setVisible(False)
        
        self.exportButton.clicked.connect(self.export)
        self.refreshButton.clicked.connect(self.refresh)
        
    def _add_button(self, layout, index, text: str, slot, icon=None) -> None:
        button = QPushButton(QIcon(icon), text, self)
        button.clicked.connect(slot)
        
        layout.insertWidget(index, button)
        return button

    def _getData(self):
        with Session(ENGINE) as session:
            statement = select(self.table)
            if self.filter is not None:
                statement = statement.where(self.filter)
            if self.joins is not None:
                for join in self.joins:
                    statement = statement.join(join)
            if self.wheres is not None:
                for where in self.wheres:
                    statement = statement.where(where)
                # print(statement)
            data = session.exec(statement).all()
        return data

    @pyqtSlot()
    def create(self):
        if self.create_dialog(parent=self.parent()).exec():
            self.refresh()

    @pyqtSlot()
    def update(self):
        self.update_dialog(self.model._data[self.selected_indexes[0]], self.parent()).exec()

    @pyqtSlot()
    def delete(self):
        if not confirm(self.parent(), "Вы действительно хотите удалить выбранные объекты?"):
            return

        with Session(ENGINE) as session:
            ids = []
            for i, j in enumerate(self.selected_indexes):
                index = j - i
                ids.append(self.model._data[index].id)
                self.model.removeRow(index)
            session.exec(delete(self.table).where(self.table.id.in_(ids)))
            session.commit()

        self.update_total_count()

    @pyqtSlot()
    def export(self):
        PATH, EXTENSION = QFileDialog.getSaveFileName(
            self, "Укажите путь", expanduser("~"), "*.csv"
        )
        if not EXTENSION:
            return

        headers = []

        for col in range(self.model.columnCount()):
            headers.append(self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))

        with open(PATH, "w", encoding="UTF-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for rowNumber in range(self.model.rowCount()):
                fields = [
                    self.model.data(
                        self.model.index(rowNumber, columnNumber), Qt.ItemDataRole.DisplayRole
                    )
                    for columnNumber in range(self.model.columnCount())
                ]
                writer.writerow(fields)

        QMessageBox.information(self, "Экспорт завершён", f"Файл был успешно сохранён в '{PATH}'.")

    @pyqtSlot()
    def refresh(self, filter=True):
        data = self._getData()
        self.model: BaseTableModel = self.table_model(data)
        self.tableView.setModel(self.model)
        self.tableView.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )
        
        if filter:
            if self.filters is not None:
                if hasattr(self, "filterBox"):
                    self.horizontalLayout_2.removeWidget(self.filterBox)
                self.filterBox = FilterBox(self.filters, self)
                self.horizontalLayout_2.addWidget(self.filterBox)

        self.on_selection_changed()
        self.update_total_count()

    @pyqtSlot()
    def on_selection_changed(self):
        count = len(self.selected_indexes)
        self.selectedRowsCountLabel.setText(str(count))
        self.deleteButton.setEnabled(count)
        self.updateButton.setEnabled(count == 1)
        self.exportButton.setEnabled(self.model.rowCount())

        for button in self._extra_buttons:
            button.setEnabled(count)

    def update_total_count(self):
        self.totalRowsCountLabel.setText(str(self.model.rowCount()))
    
    def showTypeManagerDialog(self,  _type):
        TypeManagerDialog(_type, self).exec()
        self.refresh()
        
    def add_top_button(self, text: str, slot, icon=None) -> None:
        self._add_button(self.horizontalLayout, 2, text, slot, icon)

    def add_extra_button(self, text: str, slot, icon=None) -> None:
        btn = self._add_button(self.toolbarLayout, 0, text, slot, icon)
        self._extra_buttons.append(btn)


class EventTable(Table):
    table = Event
    table_model = EventTableModel
    create_dialog = EventCreateDialog
    update_dialog = EventUpdateDialog
    # joins = (EventType,)
    filters = {
        # "Вид:": (EventType.name, QComboBox),
        "Начало:": (Event.start_at, QDateTimeEdit),
        "Дата создания:": (Event.created_at, QDateTimeEdit),
    }
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_top_button("Разновидности", lambda: self.showTypeManagerDialog(EventType), "app/ui/resourses/maximize.png")


class AssignmentTable(Table):
    table = Assignment
    table_model = AssignmentTableModel
    create_dialog = AssignmentCreateDialog
    update_dialog = AssignmentUpdateDialog
    joins = (AssignmentType, Location)
    filters = {
        "Вид:": (AssignmentType.name, QComboBox),
        "Локация:": (Location.name, QComboBox),
        "Дедлайн:": (Assignment.deadline, QDateTimeEdit),
        "Дата создания:": (Assignment.created_at, QDateTimeEdit),
    }
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_top_button("Разновидности", lambda: self.showTypeManagerDialog(AssignmentType), "app/ui/resourses/maximize.png")


class DesktopTable(AssignmentTable):
    create_dialog = None
    update_dialog = None
    filter = (Assignment.state == Assignment.State.ACTIVE)
    delete_visible = False
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_extra_button("Пометить как выполненное", self.mark_as_completed, "app/ui/resourses/check.png")
        
    def mark_as_completed(self) -> None:
        with Session(ENGINE) as session:
            assignments = []
            for i, j in enumerate(self.selected_indexes):
                index = j - i
                assignment: Assignment = self.model._data[index]
                assignment.state = Assignment.State.COMPLETED
                assignments.append(assignment)
                self.model.removeRow(index)
            session.bulk_save_objects(assignments)
            session.commit()

        self.update_total_count()
  
  
class ReservationTable(Table):
    table = Reservation
    table_model = ReservaionTableModel
    joins = (Location,)
    filters = {
        "Локация:": (Location.name, QComboBox),
        "Начало:": (Reservation.start_at, QDateTimeEdit),
        "Конец:": (Reservation.end_at, QDateTimeEdit),
        "Дата создания:": (Reservation.created_at, QDateTimeEdit),
    }
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_top_button("Разновидности", lambda: self.showTypeManagerDialog(Location), "app/ui/resourses/maximize.png")
        self.add_top_button("Зоны", self.showAreasManager, "app/ui/resourses/categorize.png")

    def showAreasManager(self):
        AreaManagerDialog(self).exec()
        self.refresh()
        
        
class EducationTable(Table):
    table = Club
    table_model = ClubTableModel
    create_dialog = ClubCreateDialog
    update_dialog = ClubUpdateDialog
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_top_button("Виды секция", lambda: self.showTypeManagerDialog(ClubType), "app/ui/resourses/maximize.png")
        self.add_top_button("Преподаватели", lambda: self.showTypeManagerDialog(Teacher), "app/ui/resourses/categorize.png")
