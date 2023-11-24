from PyQt6.QtWidgets import QWidget, QMessageBox


def validationError(parent: QWidget, message):
    QMessageBox.critical(parent, "Ошибка проверки", message)
