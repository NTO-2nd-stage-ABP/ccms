from typing import Any

from PyQt6.QtCore import (
    QObject,
    Qt,
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
)
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import func

from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import EventType, Event


class EventsTableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        with Session(ENGINE) as session:
            self.__data = session.exec(select(Event)).all()
        self.__headers = ("Заголовок", "Дата", "Тип", "Описание")

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...
    ) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.__headers[section]
        return super().headerData(section, orientation, role)
    
    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            event = self.__data[index.row()]
            match index.column():
                case 0:
                    return event.name
                case 1:
                    return event.date.strftime("%d.%M.%Y %H:%M")
                case 2:
                    with Session(ENGINE) as session:
                        type = session.exec(select(EventType.name).where(EventType.id == event.type_id)).first()
                    return type
                case 3:
                    return event.description
    
    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if self.showConfirmationWarning() != QMessageBox.StandardButton.Ok:
            return False
        
        self.beginRemoveRows(parent, row, row + count - 1)
        with Session(ENGINE) as session:
            for i in range(count):
                eventType = session.get(Event, self.__data[row + i].id)
                session.delete(eventType)
                del self.__data[row : row + count]
            session.commit()
        self.endRemoveRows()
        return True
    
    def rowCount(self, _: QModelIndex = ...) -> int:
        return len(self.__data)
    
    def columnCount(self, _: QModelIndex = ...) -> int:
        return len(self.__headers)

    def flags(self, _: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
    
    def showConfirmationWarning(self):
        return QMessageBox.warning(
            self.parent(),
            "Удаление объекта",
            "Вы действительно хотите удалить этот объект?",
            defaultButton=QMessageBox.StandardButton.Cancel,
        )


class EventTypesListModel(QAbstractListModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        with Session(ENGINE) as session:
            self.__data = session.exec(select(EventType)).all()

    def rowCount(self, _: QModelIndex = ...) -> int:
        return len(self.__data)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self.__data[index.row()].name

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        self.beginInsertRows(parent, row, row + count - 1)
        with Session(ENGINE) as session:
            for _ in range(count):
                maxId = session.query(func.max(EventType.id)).scalar()
                name = f"Вид {maxId or ''}"
                if self.eventTypeNameExists(name):
                    self.showUniqueNameWarning(name)
                    return False
                newEventType = EventType(name=name)
                session.add(newEventType)
                session.commit()
                session.refresh(newEventType)
                self.__data += [newEventType]
        self.endInsertRows()
        return True

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if not self.__data:
            QMessageBox.warning(self.parent(), "Предупреждение", "Список видов пуст.")
            return False

        if self.showConfirmationWarning() != QMessageBox.StandardButton.Ok:
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        with Session(ENGINE) as session:
            for i in range(count):
                eventType = session.get(EventType, self.__data[row + i].id)
                session.delete(eventType)
                del self.__data[row : row + count]
            session.commit()
        self.endRemoveRows()
        return True

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            if (
                self.eventTypeNameExists(value)
                and self.__data[index.row()].name != value
            ):
                self.showUniqueNameWarning(value)
                return False
            self.__data[index.row()].name = value
            with Session(ENGINE) as session:
                eventType = session.get(EventType, self.__data[index.row()].id)
                eventType.name = value
                session.add(eventType)
                session.commit()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, _: QModelIndex) -> Qt.ItemFlag:
        return (
            Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

    def eventTypeNameExists(self, name: str) -> bool:
        with Session(ENGINE) as session:
            return session.query(
                select(EventType).filter_by(name=name).exists()
            ).scalar()

    def showUniqueNameWarning(self, name: str) -> None:
        QMessageBox.warning(
            self.parent(),
            "Предупреждение",
            f"Вид мероприятий с названием '{name}' уже был создан ранее.",
        )

    def showConfirmationWarning(self):
        return QMessageBox.warning(
            self.parent(),
            "Удаление объекта",
            "Вы действительно хотите удалить этот объект?",
            defaultButton=QMessageBox.StandardButton.Cancel,
        )
