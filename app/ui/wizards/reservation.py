from enum import StrEnum, auto

from PyQt6 import QtWidgets, QtCore, uic
from sqlmodel import Session, select, exists

from app.db import ENGINE
from app.db.models import Area, Event, Place, Reservation


class Fields(StrEnum):
    START_AT = auto()
    END_AT = auto()
    PLACE_ID = auto()
    AREA_IDS = auto()
    COMMENT = auto()


class WelcomePage(QtWidgets.QWizardPage):    
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/welcome-page.ui", self)
        self.registerField(Fields.START_AT, self.startDateTimeEdit)
        self.registerField(Fields.END_AT, self.endDateTimeEdit)

    def initializePage(self) -> None:
        self.endDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
        self.startDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
    
    def validatePage(self) -> bool:
        if self.startDateTimeEdit.dateTime() >= self.endDateTimeEdit.dateTime():
            QtWidgets.QMessageBox.critical(self, "Ошибка валидации!", "Время начала должно быть больше вермени конца!")
            return False

        self.setField(Fields.START_AT, self.startDateTimeEdit.dateTime())
        self.setField(Fields.END_AT, self.endDateTimeEdit.dateTime())
        return super().validatePage()


class ResultsPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/results-page.ui", self)
        
        # self.registerField(Fields.PLACE_ID, self.listWidget)
        spin = QtWidgets.QSpinBox(self)
        spin.setVisible(False)
        self.registerField(Fields.PLACE_ID, spin)
        self.listWidget.itemSelectionChanged.connect(lambda: self.completeChanged.emit())

    def initializePage(self) -> None:
        self.listWidget.clear()

        start_at = self.field(Fields.START_AT).toPyDateTime()
        
        # Так писать нельзя, позже отрефакторю! Но оно работает :)
        with Session(ENGINE) as session:
            places = session.exec(select(Place)).all()
            free = []
            for place in places:

                # Полностью пустое
                if not(any(place.areas) or any(place.reservations)):
                    free.append(place)
                    continue

                # Бронирование не пересекается
                if any(reservation.end_at < start_at for reservation in place.reservations):

                    # Нет зон
                    if not(any(place.areas)):
                        free.append(place)
                        continue
                    
                    for area in place.areas:
                        
                        # Полностью пустое
                        if not any(area.reservations):
                            free.append(place)
                            break
                        
                        # Бронирование не пересекается
                        if any(reservation.end_at < start_at for reservation in area.reservations):
                            free.append(place)
                            break

                    continue

                for area in place.areas:
                        
                    # Полностью пустое
                    if not any(area.reservations):
                        free.append(place)
                        break
                    
                    # Бронирование не пересекается
                    if any(reservation.end_at < start_at for reservation in area.reservations):
                        free.append(place)
                        break

            names = list(place.name for place in free)

        self.listWidget.addItems(names)

        # print(start_at)
        # end_at = self.field("end_at").toPyDateTime().strftime("%d.%m.%Y %H:%M")
        # title = f"Ниже перечислены варианты бронирования на период с {start_at} до {end_at}:"
        # self.setSubTitle(title)

    def isComplete(self) -> bool:
        return bool(self.listWidget.selectedIndexes())
        
    def validatePage(self) -> bool:        
        with Session(ENGINE) as session:
            name = self.listWidget.currentItem().data(QtCore.Qt.ItemDataRole.DisplayRole)
            place_id = session.exec(select(Place.id).where(Place.name == name)).first()
            self.setField(Fields.PLACE_ID, place_id)

        return super().validatePage()


class AreasPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/areas-page.ui", self)
        self.place = None
        lst = QtWidgets.QListWidget(self)
        lst.setVisible(False)
        self.registerField(Fields.AREA_IDS, lst, "selectedItems")
        self.listWidget.itemChanged.connect(lambda: self.completeChanged.emit())

    def initializePage(self) -> None:
        self.listWidget.clear()

        start_at = self.field(Fields.START_AT).toPyDateTime()        
        place_id: int = self.field(Fields.PLACE_ID)

        with Session(ENGINE) as session:
            self.place = session.get(Place, place_id)
            for area in self.place.areas:
                item = QtWidgets.QListWidgetItem(area.name)
                
                is_busy = True
                
                # Полностью пустое
                if not any(area.reservations):
                    is_busy = False
                
                # Бронирование не пересекается
                if any(reservation.end_at < start_at for reservation in area.reservations):
                    is_busy = False
                
                flags = QtCore.Qt.ItemFlag.NoItemFlags if is_busy else QtCore.Qt.ItemFlag.ItemIsEnabled

                item.setFlags(flags | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
                self.listWidget.addItem(item)
        return super().initializePage()
    
    def isComplete(self) -> bool:
        return any(self.listWidget.item(i).checkState() == QtCore.Qt.CheckState.Checked for i in range(self.listWidget.count()))
    
    def validatePage(self) -> bool:
        names = frozenset(
            self.listWidget.item(i).data(QtCore.Qt.ItemDataRole.DisplayRole) 
            for i in range(self.listWidget.count()) 
            if self.listWidget.item(i).checkState() == QtCore.Qt.CheckState.Checked
        )
        ids = frozenset(area.id for area in self.place.areas if area.name in names)
        self.setField(Fields.AREA_IDS, ids)

        return super().validatePage()


class FinalPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/final-page.ui", self)
        self.registerField(Fields.COMMENT, self.commentTextEdit)
        
    def validatePage(self) -> bool:
        self.setField(Fields.COMMENT, self.commentTextEdit.toPlainText())
        return super().validatePage()


class ReservationWizard(QtWidgets.QWizard):
    def __init__(self, event: Event, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._event = event

        self.setWindowTitle("Мастер бронирования помещений")

        self.welcomePage = WelcomePage()
        self.resultsPage = ResultsPage()
        self.areasPage = AreasPage()
        self.finalPage = FinalPage()

        self.addPage(self.welcomePage)
        self.addPage(self.resultsPage)
        self.addPage(self.areasPage)
        self.addPage(self.finalPage)

        self.button(QtWidgets.QWizard.WizardButton.FinishButton).clicked.connect(self.createReservation)

    def nextId(self) -> int:
        if self.currentPage() != self.resultsPage:
            return super().nextId()

        place_id: int = self.field(Fields.PLACE_ID)
        with Session(ENGINE) as session:
            (ret, ), = session.query(exists().where(Area.place_id == place_id))
        
        if ret:
            return super().nextId()
        return self.currentId() + 2

    def createReservation(self):
        self.reservation = Reservation(
            start_at=self.field(Fields.START_AT).toPyDateTime(),
            end_at=self.field(Fields.END_AT).toPyDateTime(),
            comment=self.field(Fields.COMMENT),
            event_id=self._event.id,
            place_id=self.field(Fields.PLACE_ID),
        )
        
        if self.areasPage.place:
            self.reservation.areas = list(area for area in self.areasPage.place.areas if area.id in self.field(Fields.AREA_IDS))
