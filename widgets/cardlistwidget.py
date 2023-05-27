from PySide6 import QtWidgets, QtCore, QtGui

import connector
from lib import scryfall, utils

COLUMNS = ["name", "mana_cost", "set", "type_line"]


class CardListWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setColumnCount(len(COLUMNS))
        self.setHorizontalHeaderLabels(COLUMNS)
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

    def setCards(self, cardsList: list):
        # self.clear()
        self.setRowCount(0)
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            card.update({"qty": qty})
            self._addOneLine(card)

    def _addOneLine(self, card: dict):
        for i, tableItem in enumerate(getCardTableItem(card, columns=COLUMNS)):
            tableItem.setFlags(tableItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.setItem(self.rowCount() - 1, i, tableItem)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        cardId = event.source().currentItem().data(QtCore.Qt.UserRole)["id"]
        self.addCard(scryfall.getCardById(cardId))

    def addCard(self, card: dict):
        self.insertRow(self.rowCount())
        card.update({"qty": 1})
        self._addOneLine(card=card)
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


def getCardTableItem(cardData: dict, columns: list = []) -> QtWidgets.QTableWidgetItem:
    dataList = []
    if cardData is not None:
        for column in columns:
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, utils.getFromDict(cardData, column.split(".")))
            item.setData(QtCore.Qt.UserRole, cardData)
            dataList.append(item)
    return dataList
