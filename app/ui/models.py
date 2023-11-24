from typing import Any, Callable, Dict, Final, Set, Tuple, TypeVar, Generic

from PyQt6.QtCore import (
    QObject,
    Qt,
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import (
    BaseModel,
    BaseNamedModel,
    EventType,
    Event,
    WorkRequest,
    WorkRequestType,
    RoomType,
    WorkRequestStatus,
)

TBaseNamedModel = TypeVar("TBaseNamedModel", bound=BaseNamedModel)
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

    def insertRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginInsertRows(parent, row, row)

        name = f"Объект ({self.rowCount()})"

        if self.isUniqueNameConstraintFailed(name):
            self._showUniqueNameConstraintWarning(name)
            return False

        with Session(ENGINE) as session:
            newObj: TBaseNamedModel = self._getGenericType()(name=name)
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
            obj: TBaseNamedModel = session.get(self._getGenericType(), item.id)
            session.delete(obj)
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

        if self.isUniqueNameConstraintFailed(value):
            self._showUniqueNameConstraintWarning(value)
            return False

        item.name = value

        with Session(ENGINE) as session:
            obj: TBaseNamedModel = session.get(self._getGenericType(), item.id)
            obj.name = value
            session.add(obj)
            session.commit()

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


class EventTableModel(BaseTableModel[Event]):
    GENERATORS = {
        "Заголовок": lambda e: e.name,
        "Пространство": lambda e: SECTIONS[e.section.value],
        "Разновидность": lambda e: e.type.name,
        "Помещение": lambda e: e.room.name,
        "Дата начала": lambda e: e.start_at.strftime("%d.%m.%Y %H:%M"),
        "Описание": lambda e: e.description,
    }

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            event = self._data[index.row()]
            with Session(ENGINE) as session:
                session.add(event)
                return list(self.GENERATORS.values())[index.column()](event)

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)
        with Session(ENGINE) as session:
            item = self._data[row]
            eventType = session.get(Event, item.id)
            session.delete(eventType)
            self._data.remove(item)
            session.commit()
        self.endRemoveRows()
        return True


class WorkRequestTableModel(BaseTableModel[WorkRequest]):
    GENERATORS = {
        "Помещение": lambda r: r.room.name,
        "Разновидность": lambda r: r.type.name,
        "Мероприятие": lambda r: r.event.name,
        "Статус": lambda r: STATUSES[r.status.value],
        "Дедлайн": lambda r: r.deadline.strftime("%d.%m.%Y %H:%M"),
        "Дата создания": lambda r: r.created_at.strftime("%d.%m.%Y %H:%M"),
        "Описание": lambda r: r.description,
    }

    STATUS_COLORS = {
        WorkRequestStatus.DRAFT: None,
        WorkRequestStatus.ACTIVE: QColor("lightpink"),
        WorkRequestStatus.COMPLETED: QColor("lightgray"),
    }

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        workRequest: WorkRequest = self._data[index.row()]

        if role == Qt.ItemDataRole.BackgroundRole:
            return self.STATUS_COLORS[workRequest.status]

        if role == Qt.ItemDataRole.DisplayRole:
            with Session(ENGINE) as session:
                session.add(workRequest)
                return list(self.GENERATORS.values())[index.column()](workRequest)

    def removeRow(
        self, row: int, delete=True, parent: QModelIndex = QModelIndex()
    ) -> bool:
        self.beginRemoveRows(parent, row, row)
        with Session(ENGINE) as session:
            item = self._data[row]
            self._data.remove(item)
            if delete:
                workType = session.get(WorkRequest, item.id)
                session.delete(workType)
                session.commit()
        self.endRemoveRows()
        return True


__all__ = ["TypeListModel", "EventTableModel", "WorkRequestTableModel"]
