from typing import Any, Callable, Dict, Set, TypeVar, Generic

from PyQt6.QtCore import (
    QObject,
    Qt,
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox
from sqlmodel import Session

from app.db import ENGINE
from app.db.models import BaseModel, Reservation, UniqueNamedModel, Event, Assignment

TBaseNamedModel = TypeVar("TBaseNamedModel", bound=UniqueNamedModel)
TModel = TypeVar("TModel", bound=BaseModel)

SECTIONS = {1: "Развлечение", 2: "Просвещение", 3: "Образование"}

STATUSES = {1: "Черновик", 2: "Активно", 3: "Выполнено"}


class TypeListModel(Generic[TBaseNamedModel], QAbstractListModel):
    def __init__(
        self, data: Set[TBaseNamedModel], parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._data = data

    def rowCount(self, _: QModelIndex = ...) -> int:
        return len(self._data)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._data[index.row()].name

    def insertRow(
        self, row: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        self.beginInsertRows(parent, row, row)

        name = f"Объект ({self.rowCount()})"

        if self.isUniqueNameConstraintFailed(name):
            self._showUniqueNameConstraintWarning(name)
            return False

        with Session(ENGINE) as session:
            newObj: TBaseNamedModel = self._getGenericType()(name=name, **kwargs)
            session.add(newObj)
            session.commit()
            session.refresh(newObj)

        self._data.append(newObj)

        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)

        item = self._data[row]

        if (
            self._showObjectDeletionConfirmation(item.name)
            != QMessageBox.StandardButton.Ok
        ):
            return False

        self._data.remove(item)

        with Session(ENGINE) as session:
            session.add(item)
            session.delete(item)
            session.commit()

        self.endRemoveRows()
        return True

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            return self.editData(index, value)

    def editData(self, index: QModelIndex, value: Any) -> bool:
        item = self._data[index.row()]

        if item.name == value:
            return False

        if value == "" or self.isUniqueNameConstraintFailed(value):
            self._showUniqueNameConstraintWarning(value)
            return False

        with Session(ENGINE) as session:
            session.add(item)
            item.name = value
            session.commit()
            session.refresh(item)

        self.dataChanged.emit(index, index)
        return True

    def flags(self, _: QModelIndex) -> Qt.ItemFlag:
        return (
            Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

    def isUniqueNameConstraintFailed(self, name: str) -> bool:
        return any(item.name == name for item in self._data)

    def _showUniqueNameConstraintWarning(self, name: str) -> None:
        QMessageBox.critical(
            self.parent(), "Ошибка", f"Объект названием '{name}' уже был создан ранее."
        )

    def _showObjectDeletionConfirmation(self, name: str) -> bool:
        return QMessageBox.warning(
            self.parent(),
            "Подтверждение удаления объекта",
            f"Вы действительно хотите удалить '{name}'?",
            defaultButton=QMessageBox.StandardButton.Close,
        )

    def _getGenericType(self) -> TBaseNamedModel:
        return self.__orig_class__.__args__[0]


class BaseTableModel(Generic[TModel], QAbstractTableModel):
    GENERATORS: Dict[str, Callable[[TModel], Any]] | None = None

    def __init__(self, data: Set[TModel], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data = data
        self._headers = list(self.GENERATORS.keys())

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...
    ) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._headers[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, _: QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, _: QModelIndex = ...) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            item = self._data[index.row()]
            with Session(ENGINE) as session:
                session.add(item)
                return list(self.GENERATORS.values())[index.column()](item)

    # def insertRow(self, row: int, parent: QModelIndex = QModelIndex(), dlg=None) -> bool:
    #     self.beginInsertRows(parent, row, row)

    #     name = f"Объект ({self.rowCount()})"

    #     # if self.isUniqueNameConstraintFailed(name):
    #         # self._showUniqueNameConstraintWarning(name)
    #         # return False

    #     with Session(ENGINE) as session:
    #         newObj: TBaseNamedModel = self._getGenericType()(name=name)
    #         session.add(newObj)
    #         session.commit()
    #         session.refresh(newObj)

    #     self._data.append(newObj)

    #     self.endInsertRows()
    #     return True

    def removeRow(
        self, row: int, delete=True, parent: QModelIndex = QModelIndex()
    ) -> bool:
        self.beginRemoveRows(parent, row, row)
        with Session(ENGINE) as session:
            item = self._data[row]
            self._data.remove(item)
            if delete:
                session.add(item)
                session.delete(item)
                session.commit()
        self.endRemoveRows()
        return True


class EventTableModel(BaseTableModel[Event]):
    GENERATORS = {
        "Заголовок": lambda e: e.title,
        "Пространство": lambda e: SECTIONS[e.scope.value],
        "Разновидность": lambda e: e.type.name if e.type else None,
        "Помещение": lambda e: str.join(", ", (r.place.name for r in e.reservations)) if any(e.reservations) else None,
        "Дата начала": lambda e: e.start_at.strftime("%d.%m.%Y %H:%M"),
        "Дата создания": lambda e: e.created_at.strftime("%d.%m.%Y %H:%M"),
        "Описание": lambda e: e.description,
    }


class AssignmentTableModel(BaseTableModel[Assignment]):
    GENERATORS = {
        "Помещение": lambda a: a.place.name if a.place else None,
        "Разновидность": lambda a: a.type.name,
        "Мероприятие": lambda a: a.event.title if a.event else None,
        "Статус": lambda a: STATUSES[a.state.value],
        "Дедлайн": lambda a: a.deadline.strftime("%d.%m.%Y %H:%M"),
        "Дата создания": lambda a: a.created_at.strftime("%d.%m.%Y %H:%M"),
        "Описание": lambda a: a.description,
    }

    STATUS_COLORS = {
        Assignment.State.DRAFT: None,
        Assignment.State.ACTIVE: QColor("lightpink"),
        Assignment.State.COMPLETED: QColor("lightgray"),
    }

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role != Qt.ItemDataRole.BackgroundRole:
            return super().data(index, role)

        workRequest: Assignment = self._data[index.row()]
        return self.STATUS_COLORS[workRequest.state]


class ReservaionTableModel(BaseTableModel[Reservation]):
    GENERATORS = {
        "Помещение": lambda r: r.place.name if r.place else None,
        "Зоны": lambda r: str.join(", ", (a.name for a in r.areas)) if any(r.areas) else None,
        "Мероприятие": lambda r: r.event.title if r.event else None,
        "Дата начала": lambda r: r.start_at.strftime("%d.%m.%Y %H:%M"),
        "Дата конца": lambda r: r.end_at.strftime("%d.%m.%Y %H:%M"),
        "Комментарий": lambda r: r.comment,
        "Дата создания": lambda r: r.created_at.strftime("%d.%m.%Y %H:%M"),
    }


__all__ = [
    "TypeListModel",
    "EventTableModel",
    "AssignmentTableModel",
    "ReservaionTableModel",
]
