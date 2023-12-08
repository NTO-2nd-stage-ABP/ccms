import csv
from functools import reduce

from os.path import expanduser

import typing
from sqlmodel import Session, Column, select, delete
from sqlalchemy.orm import class_mapper
from sqlmodel.sql.expression import SelectOfScalar

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QMessageBox, QFileDialog, QPushButton
from app.ui.widgets.alerts import confirm

from app.ui.widgets.dialogs import TypeManagerDialog
from app.db import ENGINE
from app.ui.models import BaseTableModel
from app.db.models import BaseModel
from app.ui.widgets.mixins import WidgetMixin
from app.ui.widgets.tables.filters import Filter, FilterBox

# _T = typing.TypeVar("_T", BaseModel)
# typing.Generic(_T), 

class Table(QWidget, WidgetMixin):
    ui_path = "app/ui/assets/table.ui"

    table: BaseModel
    table_model: BaseTableModel
    create_dialog: QDialog | None = None
    update_dialog: QDialog | None = None
    delete_visible: bool = True
    filters: tuple[Filter] = None
    
    @property
    def selected_indexes(self):
        return sorted(i.row() for i in self.tableView.selectionModel().selectedRows())

    @property
    def statement(self):
        statement: SelectOfScalar = select(self.table)
        if self._filter_box and self._filter_box.where is not None:
            joins = (flt._statement.parent.class_ for flt in self.filters if not isinstance(flt._statement.parent.class_(), self.table))
            statement = reduce(lambda s, j: s.join(j, isouter=True), joins, statement).where(self._filter_box.where)
        return statement
        
    @property
    def data(self):
        with Session(ENGINE) as session:
            return session.exec(self.statement).all()
    
    def __init__(self, parent: QWidget | None = None) -> None:
        self._extra_buttons = []
        super().__init__(parent)
        self._filter_box = FilterBox(self.filters, self) if self.filters else None
        
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
        self.model: BaseTableModel = self.table_model(self.data)
        self.tableView.setModel(self.model)
        self.tableView.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )
        
        if filter and self._filter_box:
            self.horizontalLayout_2.removeWidget(self._filter_box)
            self._filter_box = FilterBox(self.filters, self)
            self.horizontalLayout_2.addWidget(self._filter_box)

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
