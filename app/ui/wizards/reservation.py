from PyQt6 import QtWidgets, QtCore, uic
from sqlmodel import Session, select

from app.db import ENGINE
from app.db.models import Place


class WelcomePage(QtWidgets.QWizardPage):    
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/welcome-page.ui", self)
        self.registerField("start_at", self.startDateTimeEdit)
        self.registerField("end_at", self.endDateTimeEdit)

    def initializePage(self) -> None:
        self.endDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
        self.startDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
    
    def validatePage(self) -> bool:
        if self.startDateTimeEdit.dateTime() >= self.endDateTimeEdit.dateTime():
            QtWidgets.QMessageBox.critical(self, "Ошибка валидации!", "Время начала должно быть больше вермени конца!")
            return False

        self.setField("start_at", self.startDateTimeEdit.dateTime())
        self.setField("end_at", self.endDateTimeEdit.dateTime())
        return True
        


class ResultsPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/results-page.ui", self)

    def initializePage(self) -> None:
        with Session(ENGINE) as session:
            roomTypeNames = session.exec(select(Place.name)).all()
        self.listWidget.addItems(roomTypeNames)
        # start_at = self.field("start_at").toPyDateTime().strftime("%d.%m.%Y %H:%M")
        # end_at = self.field("end_at").toPyDateTime().strftime("%d.%m.%Y %H:%M")
        # title = f"Ниже перечислены варианты бронирования на период с {start_at} до {end_at}:"
        # self.setSubTitle(title)


class FinalPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/wizards/final-page.ui", self)


class ReservationWizard(QtWidgets.QWizard):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Мастер бронирования помещений")

        self.welcomePage = WelcomePage()
        self.addPage(self.welcomePage)
        self.resultsPage = ResultsPage()
        self.addPage(self.resultsPage)
        self.finalPage = FinalPage()
        self.addPage(self.finalPage)

        self.button(QtWidgets.QWizard.WizardButton.FinishButton).clicked.connect(self.createReservation)

    def createReservation(self):
        pass
