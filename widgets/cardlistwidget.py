from PySide6 import QtWidgets, QtCore, QtGui

import connector
from lib import scryfall, utils

COLUMNS = ["name", "mana_cost", "type_line", "sets"]
USER_COLUMNS = ["qty", "name", "mana_cost", "type_line", "set"]


class CardListWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, columns=COLUMNS) -> None:
        super().__init__(parent)
        self.columns = columns
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setHorizontalHeaderLabels(self.columns)

    def setCards(self, cardsList: list):
        self.setRowCount(0)
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            card.update({"qty": qty})
            # handle reprints
            sets = scryfall.getCardReprints(card["id"])
            card.update({"sets": sets})
            self._addOneLine(card)

    def _addOneLine(self, card: dict):
        for i, tableItem in enumerate(self.getCardTableItem(card, columns=self.columns)):
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

    def getCardTableItem(self, cardData: dict, columns: list = []) -> QtWidgets.QTableWidgetItem:
        dataList = []
        if cardData is not None:
            for column in columns:
                item = QtWidgets.QTableWidgetItem()
                text = utils.getFromDict(cardData, column.split("."))
                # mana cost handling # TODO handle split/phyrexian mana
                if column == "mana_cost":
                    item.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        self.parent().parent().parent().parent().parent().parent().manaFontId
                    )))
                    text = utils.setManaText(str(text))
                # Set(s) handling
                if column == "sets" and "sets" in cardData.keys():
                    item.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        self.parent().parent().parent().parent().parent().parent().keyruneFontId
                    )))
                    text = utils.setSetsText(text)
                if column == "set" and "set" in cardData.keys():
                    item.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        self.parent().parent().parent().parent().parent().parent().keyruneFontId
                    )))
                    text = utils.setSetsText([text])
                item.setData(QtCore.Qt.DisplayRole, text)
                item.setData(QtCore.Qt.UserRole, cardData)
                dataList.append(item)
        return dataList


class CardStackListWidget(CardListWidget):
    # similar to the cardListWidget but whith specific data about qties, user comments, etc...
    def __init__(self, parent=None, columns=USER_COLUMNS) -> None:
        super().__init__(parent, columns=columns)
        self.columns = columns
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setHorizontalHeaderLabels(self.columns)

    def setCardList(self, cardList: connector.Deck | connector.Collection):
        self.setRowCount(0)
        self.cardStack = []
        for qty, card in cardList:
            self.cardStack.append((qty, scryfall.getCardById(card)))
        self.setCards(self.cardStack)
