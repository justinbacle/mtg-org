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
        for qty, card in cardsList:
            self.addItem(getCardWidgetListItem(qty, card))

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        cardId = event.source().currentItem().data(QtCore.Qt.UserRole)["id"]
        self.addCard(scryfall.getCardById(cardId))

    def addCard(self, card: str):
        self.addItem(getCardWidgetListItem(qty=1, cardData=card))
        stackType, stackName = self.parent().parent().parent().parent().parent().parent().deckSelector.getSelected()
        if stackType == "deck":
            connector.addCardToDeck(stackName, 1, card["id"])
        elif stackType == "collection":
            connector.addCardToCollection(stackName, 1, card["id"])
        else:
            ...


class CardStackListWidget(CardListWidget):
    # similar to the cardListWidget but whith specific data about qties, user comments, etc...
    def __init__(self, parent=None) -> None:
        self.cardStack = None
        super().__init__(parent)

    def setCardList(self, cardList: connector.Deck | connector.Collection):
        self.cardStack = []
        for qty, card in cardList:
            self.cardStack.append(
                (qty, scryfall.getCardById(card))
            )
        self.setCards(self.cardStack)


def getCardWidgetListItem(qty: 1, cardData: dict) -> QtWidgets.QListWidgetItem:
    if cardData is not None:
        item = QtWidgets.QListWidgetItem(cardData["name"])
        cardData.update({"qty": 1})
        item.setData(QtCore.Qt.UserRole, cardData)
    else:
        item = None
    return item
