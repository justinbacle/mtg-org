from PySide6 import QtWidgets, QtCore, QtGui

import connector
from lib import scryfall


class CardListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

    def setCards(self, cardsList: list):
        self.clear()
        for card in cardsList:
            self.addItem(getCardWidgetListItem(card))

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        cardId = event.source().currentItem().data(QtCore.Qt.UserRole)["id"]
        self.addCard(scryfall.getCardById(cardId))

    def addCard(self, card: str):
        self.addItem(getCardWidgetListItem(card))
        stackType, stackName = self.parent().parent().parent().parent().parent().parent().deckSelector.getSelected()
        if stackType == "deck":
            connector.addCardToDeck(stackName, card["id"])
        elif stackType == "collection":
            connector.addCardToCollection(stackName, card["id"])
        else:
            ...


class CardStackListWidget(CardListWidget):
    # similar to the cardListWidget but whith specific data about qties, user comments, etc...
    def __init__(self, parent=None) -> None:
        self.cardStack = None
        super().__init__(parent)

    def setCardList(self, cardList: connector.Deck | connector.Collection):
        self.cardStack = [scryfall.getCardById(card) for card in cardList]
        # ? To update to handle quantities etc ???
        self.setCards(self.cardStack)


def getCardWidgetListItem(cardData: dict) -> QtWidgets.QListWidgetItem:
    if cardData is not None:
        item = QtWidgets.QListWidgetItem(cardData["name"])
        item.setData(QtCore.Qt.UserRole, cardData)
    else:
        item = None
    return item
