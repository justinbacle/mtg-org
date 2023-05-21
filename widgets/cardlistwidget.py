from PySide6 import QtWidgets


class CardListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
