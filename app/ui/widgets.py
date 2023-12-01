from PyQt6 import uic


class WidgetMixin:
    """
    Adds `windowTitle` in the current widget.
    """

    title = None
    ui_path = None
    
    def __init__(self) -> None:
        if self.ui_path:
            uic.loadUi(self.ui_path, self)

        self.setWindowTitle(self.get_title())
        self.setup_ui()
        
    def setup_ui(self):
        pass
    
    def get_title(self):
        return self.title
