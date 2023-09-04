from PySide6 import QtWidgets, QtCore, QtGui
from tqdm import tqdm

import connector
from lib import scryfall, utils, qt
import constants

COLUMNS = ["name", "mana_cost", "type_line", "set", "rarity", "price"]
USER_COLUMNS = ["qty", "name", "mana_cost", "type_line", "set", "rarity", "price"]


class CardSearchListWidget(QtWidgets.QTableWidget):
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

    def updateCardListInfos(self):
        # TODO update cardStack before
        self.setCards(cardsList=self.cardStack)

    def _addOneLine(self, card: dict):
        for i, tableItem in enumerate(self.getCardTableItem(card, columns=self.columns)):
            # tableItem.setFlags(tableItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.setItem(self.rowCount() - 1, i, tableItem)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.source() != self:
            cardId = event.source().currentItem().data(QtCore.Qt.UserRole)["id"]
            self.addCard(scryfall.getCardById(cardId))

    def setCards(self, cardsList: list):
        self.setRowCount(0)
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            card.update({"qty": qty})
            self._addOneLine(card)

    def getCardTableItem(self, cardData: dict, columns: list = []) -> QtWidgets.QTableWidgetItem:
        dataList = []
        if cardData is not None:
            for column in columns:
                item = QtWidgets.QTableWidgetItem()
                if column == "name" and "printed_name" in cardData.keys():
                    text = utils.getFromDict(cardData, ["printed_name"])
                else:
                    text = utils.getFromDict(cardData, column.split("."))
                if column == "qty":
                    flag = QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled | \
                        QtCore.Qt.ItemFlag.ItemIsEditable
                    item.setFlags(flag)
                else:
                    flag = QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
                    item.setFlags(flag)
                # mana cost handling
                if "card_faces" in cardData.keys():
                    if column == "mana_cost":
                        text = cardData["card_faces"][0][column]
                if column == "mana_cost":
                    font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        qt.findAttrInParents(self, "proxyglyphFontId")))
                    font.setPointSize(14)
                    item.setFont(font)
                    text = utils.setManaText(text)
                # Set(s) handling
                if column == "sets" and "sets" in cardData.keys():
                    font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        qt.findAttrInParents(self, "keyruneFontId")
                    ))
                    font.setPointSize(14)
                    item.setFont(font)
                    text = utils.setSetsText(text)
                if column == "set" and "set" in cardData.keys():
                    font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                        qt.findAttrInParents(self, "keyruneFontId")
                    ))
                    font.setPointSize(14)
                    item.setFont(font)
                    text = utils.setSetsText([text])
                if column == "price":
                    text = utils.getFromDict(cardData, ["prices", constants.CURRENCY[0]])
                    if text is not None:
                        text += " " + constants.CURRENCY[1]
                    else:
                        text = "?"
                item.setData(QtCore.Qt.DisplayRole, text)
                item.setData(QtCore.Qt.UserRole, {"data": cardData, "column": column})
                dataList.append(item)
        return dataList


class CardStackListWidget(CardSearchListWidget):
    # similar to the cardListWidget but whith specific data about qties, user comments, etc...
    def __init__(self, parent=None, columns=USER_COLUMNS) -> None:
        super().__init__(parent=parent, columns=columns)
        self.columns = columns
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setHorizontalHeaderLabels(self.columns)
        self.setMouseTracking(True)

    def on_itemChanged(self, item):
        # TODO prepare for user info (commander/sideboard/maybeboard etc...)
        if len(self.selectedItems()) == 1:
            if item.data(QtCore.Qt.UserRole)["column"] == "qty":
                previousQty = item.data(QtCore.Qt.UserRole)["data"]["qty"]
                newQty = int(item.text())
                if previousQty != newQty:
                    if previousQty > newQty:
                        self.removeQty(previousQty - newQty)
                    else:
                        self.addQty(newQty - previousQty)

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
        self.parent().sort()
        self.updateCardListInfos()

    def removeQty(self, qty: int):
        selectedLine = self.selectedIndexes()[0]
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.UserRole)["data"]
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if selectedCard["qty"] > qty:
            if stackType == "deck":
                connector.changeCardDeckQty(stackName, selectedCard["qty"] - qty, selectedCard["id"])
                deck = connector.getDeck(stackName)
                self.setCardList(deck["cardList"])
            elif stackType == "collection":
                connector.changeCardCollectionQty(stackName, selectedCard["qty"] - qty, selectedCard["id"])
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
        self.parent().sort()

    def addQty(self, qty: int):
        selectedLine = self.selectedIndexes()[0]
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.UserRole)["data"]
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.changeCardDeckQty(stackName, selectedCard["qty"] + qty, selectedCard["id"])
            deck = connector.getDeck(stackName)
            self.setCardList(deck["cardList"])
        elif stackType == "collection":
            connector.changeCardCollectionQty(stackName, selectedCard["qty"] + qty, selectedCard["id"])
            collection = connector.getCollection(stackName)
            self.setCardList(collection["cardList"])
        else:
            ...
        self.setCurrentCell(selectedLine.row(), selectedLine.column())

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_Minus:
            self.removeQty(qty=1)
        elif event.key() == QtCore.Qt.Key_Plus:
            self.addQty(qty=1)
        else:
            return super().keyPressEvent(event)

    def setCards(self, cardsList: list):
        self.setRowCount(0)
        manaValues = [0, 0, 0, 0, 0, 0, 0]  # 0, 1, 2, 3, 4, 5, 6+
        cardCount = 0
        totalPrice = 0
        colorPie = {}
        typePie = {}
        legalities = {}
        totalCmc = 0
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            card.update({"qty": qty})
            self._addOneLine(card)
            if not card["type_line"].startswith("Land") and not card["type_line"].startswith("Basic Land"):
                # manaCost
                if card["cmc"] > 6:
                    manaValues[6] = manaValues[6] + qty
                else:
                    manaValues[int(card["cmc"])] = manaValues[int(card["cmc"])] + qty
                totalCmc += int(card["cmc"])
                # colorPie
                colorIdentity = "".join(sorted("".join(card["color_identity"])))
                if colorIdentity in colorPie.keys():
                    colorPie[colorIdentity] += qty
                else:
                    colorPie.update({colorIdentity: qty})
            # cardCount
            cardCount += qty
            # cardPrice
            cardPrice = utils.getFromDict(card, ["prices", constants.CURRENCY[0]])
            if cardPrice is not None:
                totalPrice += qty * float(cardPrice)
            # typePie
            if "—" in card["type_line"]:
                cardType = card["type_line"].split("—")[0].rstrip()
            else:
                cardType = card["type_line"]
            if cardType in typePie.keys():
                typePie[cardType] += qty
            else:
                typePie.update({cardType: qty})
            # legality
            for format, legality in card["legalities"].items():
                if legality not in ["legal", "not_legal", "restricted", "banned"]:
                    raise NotImplementedError(f"{legality=} is an unupported legality type")
                elif format in legalities.keys():
                    # TODO handle "restricted"
                    if legality == "legal" and legalities[format] == "legal":
                        ...
                    else:
                        legalities[format] = "not_legal"
                else:
                    legalities.update({format: legality})
                # TODO: Handle card numbers, and format specific restrictions.

        updateDict = {
            "manaValues": manaValues,
            "cardCount": cardCount,
            "totalCmc": totalCmc,
            "totalPrice": totalPrice,
            "colorPie": colorPie,
            "typePie": typePie,
            "legalities": legalities
        }
        # TODO only trigger for cardStack
        qt.findAttrInParents(self, "decklist").infoPanel.updateValues(updateDict)
