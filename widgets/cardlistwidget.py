from PySide6 import QtWidgets, QtCore, QtGui
from tqdm import tqdm

import connector
from lib import scryfall, utils, qt
import constants

COLUMNS = ["name", "mana_cost", "type_line", "set", "rarity", "price"]
USER_COLUMNS = ["qty", "name", "mana_cost", "type_line", "set", "rarity", "price"]


class CardListWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, columns=COLUMNS) -> None:
        super().__init__(parent)
        self.columns = columns
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        # self.setSortingEnabled(True)  # TODO bugs on add/delete line ?
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setHorizontalHeaderLabels(self.columns)

    def setCards(self, cardsList: list):
        self.setRowCount(0)
        manaValues = [0, 0, 0, 0, 0, 0, 0]  # 0, 1, 2, 3, 4, 5, 6+
        cardCount = 0
        totalPrice = 0
        colorPie = {}
        typePie = {}
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            card.update({"qty": qty})
            self._addOneLine(card)
            # manaCost
            if card["cmc"] > 6:
                manaValues[6] = manaValues[6] + qty
            else:
                manaValues[int(card["cmc"])] = manaValues[int(card["cmc"])] + qty
            # cardCount
            cardCount += qty
            # cardPrice
            cardPrice = utils.getFromDict(card, ["prices", constants.CURRENCY[0]])
            if cardPrice is not None:
                totalPrice += qty * float(cardPrice)
            # colorPie
            colorIdentity = "".join(sorted("".join(card["color_identity"])))
            if colorIdentity in colorPie.keys():
                colorPie[colorIdentity] += qty
            else:
                colorPie.update({colorIdentity: qty})
            # typePie
            if "—" in card["type_line"]:
                cardType = card["type_line"].split("—")[0].rstrip()
            else:
                cardType = card["type_line"]
            if cardType in typePie.keys():
                typePie[cardType] += qty
            else:
                typePie.update({cardType: qty})
        updateDict = {
            "manaValues": manaValues,
            "cardCount": cardCount,
            "totalPrice": totalPrice,
            "colorPie": colorPie,
            "typePie": typePie
        }
        qt.findAttrInParents(self, "infoPanel").updateValues(updateDict)

    def updateCardListInfos(self):
        # TODO update cardStack before
        self.setCards(cardsList=self.cardStack)

    def _addOneLine(self, card: dict):
        for i, tableItem in enumerate(self.getCardTableItem(card, columns=self.columns)):
            tableItem.setFlags(tableItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.setItem(self.rowCount() - 1, i, tableItem)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.source() != self:
            cardId = event.source().currentItem().data(QtCore.Qt.UserRole)["id"]
            self.addCard(scryfall.getCardById(cardId))

    def getCardTableItem(self, cardData: dict, columns: list = []) -> QtWidgets.QTableWidgetItem:
        dataList = []
        if cardData is not None:
            for column in columns:
                item = QtWidgets.QTableWidgetItem()
                if column == "name" and "printed_name" in cardData.keys():
                    text = utils.getFromDict(cardData, ["printed_name"])
                else:
                    text = utils.getFromDict(cardData, column.split("."))
                # mana cost handling
                # TODO handle split/phyrexian mana
                # TODO handle mana of dual faced cards ?
                # TODO better handle parent thing
                if column == "mana_cost":
                    item.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        qt.findAttrInParents(self, "manaFontId")
                    )))
                    text = utils.setManaText(str(text))
                # Set(s) handling
                if column == "sets" and "sets" in cardData.keys():
                    item.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        qt.findAttrInParents(self, "keyruneFontId")
                    )))
                    text = utils.setSetsText(text)
                if column == "set" and "set" in cardData.keys():
                    item.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        qt.findAttrInParents(self, "keyruneFontId")
                    )))
                    text = utils.setSetsText([text])
                if column == "price":
                    text = utils.getFromDict(cardData, ["prices", constants.CURRENCY[0]])
                    if text is not None:
                        text += " " + constants.CURRENCY[1]
                    else:
                        text = "?"
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
        for qty, card in tqdm(cardList):
            self.cardStack.append((qty, scryfall.getCardById(card)))
        self.setCards(self.cardStack)

    def addCard(self, card: dict):
        self.insertRow(self.rowCount())
        card.update({"qty": 1})
        self._addOneLine(card=card)
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.addCardToDeck(stackName, 1, card["id"])
        elif stackType == "collection":
            connector.addCardToCollection(stackName, 1, card["id"])
        else:
            ...
        self.cardStack.append((1, card))
        self.updateCardListInfos()

    def removeOne(self):
        selectedLine = self.selectedIndexes()[0]
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.UserRole)
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if selectedCard["qty"] > 1:
            if stackType == "deck":
                connector.changeCardDeckQty(stackName, selectedCard["qty"] - 1, selectedCard["id"])
                deck = connector.getDeck(stackName)
                self.setCardList(deck["cardList"])
            elif stackType == "collection":
                connector.changeCardCollectionQty(stackName, selectedCard["qty"] - 1, selectedCard["id"])
                collection = connector.getCollection(stackName)
                self.setCardList(collection["cardList"])
            else:
                ...
            self.setCurrentCell(selectedLine.row(), selectedLine.column())
        else:
            if stackType == "deck":
                connector.removeCardFromDeck(stackName, selectedCard["id"])
                deck = connector.getDeck(stackName)
                self.setCardList(deck["cardList"])
            elif stackType == "collection":
                connector.removeCardFromCollection(stackName, selectedCard["id"])
                collection = connector.getCollection(stackName)
                self.setCardList(collection["cardList"])
            else:
                ...

    def addOne(self):
        selectedLine = self.selectedIndexes()[0]
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.UserRole)
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.changeCardDeckQty(stackName, selectedCard["qty"] + 1, selectedCard["id"])
            deck = connector.getDeck(stackName)
            self.setCardList(deck["cardList"])
        elif stackType == "collection":
            connector.changeCardCollectionQty(stackName, selectedCard["qty"] + 1, selectedCard["id"])
            collection = connector.getCollection(stackName)
            self.setCardList(collection["cardList"])
        else:
            ...
        self.setCurrentCell(selectedLine.row(), selectedLine.column())

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_Minus:
            self.removeOne()
        elif event.key() == QtCore.Qt.Key_Plus:
            self.addOne()
        else:
            return super().keyPressEvent(event)
