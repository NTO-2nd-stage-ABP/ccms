from PyQt6 import uic
from PyQt6.QtWidgets import QDialog


class TypeManagerDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('app/ui/dialogs/events_type_manager.ui', self)


class CreateActionDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('app/ui/dialogs/event_edit.ui', self)
