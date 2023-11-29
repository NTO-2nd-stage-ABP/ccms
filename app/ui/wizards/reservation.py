from enum import StrEnum, auto

from PyQt6 import QtWidgets, QtCore, uic
from sqlmodel import Session, select, exists

from app.db import ENGINE
from app.db.models import Area, Place


class Fields(StrEnum):
    START_AT = auto()
    END_AT = auto()
    PLACE_ID = auto()


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
        self.listWidget.selectionModel().selectionChanged.connect(lambda: self.completeChanged.emit())

    def initializePage(self) -> None:
        self.listWidget.clear()
        with Session(ENGINE) as session:
            roomTypeNames = session.exec(select(Place.name)).all()
        self.listWidget.addItems(roomTypeNames)

        # start_at = self.field(Fields.START_AT).toPyDateTime().strftime("%d.%m.%Y %H:%M")
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
        self.listWidget.itemChanged.connect(lambda: self.completeChanged.emit())

    def initializePage(self) -> None:
        self.listWidget.clear()
        
        place_id: int = self.field(Fields.PLACE_ID)
        with Session(ENGINE) as session:
            place = session.get(Place, place_id)
            for area in place.areas:
                item = QtWidgets.QListWidgetItem(area.name)
                enabled = QtCore.Qt.ItemFlag.NoItemFlags if area.event_id else QtCore.Qt.ItemFlag.ItemIsEnabled
                item.setFlags(enabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
                self.listWidget.addItem(item)    
        return super().initializePage()
    
    def isComplete(self) -> bool:
        return any(self.listWidget.item(i).checkState() == QtCore.Qt.CheckState.Checked for i in range(self.listWidget.count()))


class FinalPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/final-page.ui", self)


class ReservationWizard(QtWidgets.QWizard):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

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

        # print("оно как сюда заходит не надо когда?")
        
        if ret:
            return super().nextId()
        return self.currentId() + 2

    def createReservation(self):
        pass
