from PySide6 import QtWidgets, QtCore


class CardListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def setData(self, cardsList: list):
        for card in cardsList:
            self.addItem(getCardWidgetListItem(card))


def getCardWidgetListItem(cardData: dict) -> QtWidgets.QListWidgetItem:
    if cardData is not None:
        item = QtWidgets.QListWidgetItem(cardData["name"])
        item.setData(QtCore.Qt.UserRole, cardData)
    else:
        item = None
    return item
