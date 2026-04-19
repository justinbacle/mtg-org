from PySide6 import QtWidgets, QtCore, QtGui
from tqdm import tqdm

import connector
from lib import scryfall, utils, qt
import constants


class CardLoaderWorker(QtCore.QObject):
    cardLoaded = QtCore.Signal(int, dict)   # (qty, card_dict)
    finished = QtCore.Signal()

    def __init__(self, cardList):
        super().__init__()
        self._cardList = cardList

    def run(self):
        for qty, cardId in self._cardList:
            card = scryfall.getCardById(cardId)
            if card is not None:
                self.cardLoaded.emit(qty, card)
        self.finished.emit()

COLUMNS = ["name", "mana_cost", "type_line", "set", "rarity", "price"]
USER_COLUMNS = ["qty", "name", "mana_cost", "type_line", "set", "rarity", "price"]


class CardSearchListWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, columns=COLUMNS) -> None:
        super().__init__(parent)
        self.columns = columns
        self.cardStack: list = []
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        # self.setSortingEnabled(True)  # TODO bugs on add/delete line ?
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)  # ? Not working with selection
        self.setHorizontalHeaderLabels(self.columns)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

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
            source = event.source()
            if isinstance(source, QtWidgets.QTableWidget) and source.currentItem() is not None:
                cardId = source.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)["id"]
                card = scryfall.getCardById(cardId)
                if card is not None:
                    self.addCard(card)

    def setCards(self, cardsList: list):
        self.setRowCount(0)
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            card.update({"qty": qty})
            self._addOneLine(card)
        self.resizeColumnsToContents()

    def addCard(self, card: dict) -> None:
        raise NotImplementedError

    def getCardTableItem(self, cardData: dict, columns: list = []) -> list[QtWidgets.QTableWidgetItem]:
        dataList = []
        if cardData is not None:
            for column in columns:
                item = QtWidgets.QTableWidgetItem()
                if column == "name" and "printed_name" in cardData.keys():
                    text = utils.getFromDict(cardData, ["printed_name"])
                    if cardData["lang"] == "ph":
                        phyrexianFont = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                            qt.findAttrInParents(self, "phyrexianFontId")
                        ))
                        item.setFont(phyrexianFont)
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
                    _foil_key = constants.CURRENCY[0] + "_foil"
                    if text is not None:
                        text = str(text) + " " + constants.CURRENCY[1]
                    elif utils.getFromDict(cardData, ["prices", _foil_key]) is not None:
                        text = str(utils.getFromDict(cardData, ["prices", _foil_key])) + " " + constants.CURRENCY[1] + " (foil)"
                    else:
                        text = "N/A"
                item.setData(QtCore.Qt.ItemDataRole.DisplayRole, text)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, {"data": cardData, "column": column})
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
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.setHorizontalHeaderLabels(self.columns)
        self.setMouseTracking(True)

    def on_itemChanged(self, item):
        # TODO prepare for user info (commander/sideboard/maybeboard etc...)
        if len(self.selectedItems()) == 1:
            if item.data(QtCore.Qt.ItemDataRole.UserRole)["column"] == "qty":
                previousQty = item.data(QtCore.Qt.ItemDataRole.UserRole)["data"]["qty"]
                newQty = int(item.text())
                if previousQty != newQty:
                    if previousQty > newQty:
                        self.removeQty(previousQty - newQty)
                    else:
                        self.addQty(newQty - previousQty)

    def setCardList(self, cardList: connector.Deck | connector.Collection):
        self.setRowCount(0)
        self.cardStack = []
        _loadingBar = qt.findAttrInParents(self, 'deckLoadingBar')
        if _loadingBar is not None:
            _loadingBar.setRange(0, len(cardList))
            _loadingBar.setValue(0)
            _loadingBar.setVisible(True)

        self._loader_thread = QtCore.QThread()
        self._loader_worker = CardLoaderWorker(cardList)
        self._loader_worker.moveToThread(self._loader_thread)

        self._loader_thread.started.connect(self._loader_worker.run)
        self._loader_worker.cardLoaded.connect(self._on_card_loaded)
        self._loader_worker.finished.connect(self._loader_thread.quit)
        self._loader_worker.finished.connect(self._loader_worker.deleteLater)
        self._loader_thread.finished.connect(self._loader_thread.deleteLater)
        self._loader_worker.finished.connect(self.updateCardListInfos)

        self._loader_thread.start()

    def _on_card_loaded(self, qty: int, card: dict):
        self.cardStack.append((qty, card))
        self.insertRow(self.rowCount())
        card.update({"qty": qty})
        self._addOneLine(card)
        _loadingBar = qt.findAttrInParents(self, 'deckLoadingBar')
        if _loadingBar is not None:
            _loadingBar.setValue(_loadingBar.value() + 1)

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
        self.parent().parent().parent().sort()  # type: ignore[union-attr]
        self.updateCardListInfos()

    def removeQty(self, qty: int):
        selectedLine = self.selectedIndexes()[0]
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.ItemDataRole.UserRole)["data"]
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if selectedCard["qty"] > qty:
            if stackType == "deck":
                connector.changeCardDeckQty(stackName, selectedCard["qty"] - qty, selectedCard["id"])
                deck = connector.getDeck(stackName)
                if deck is not None:
                    self.setCardList(deck["cardList"])
            elif stackType == "collection":
                connector.changeCardCollectionQty(stackName, selectedCard["qty"] - qty, selectedCard["id"])
                collection = connector.getCollection(stackName)
                if collection is not None:
                    self.setCardList(collection["cardList"])
            else:
                ...
            self.setCurrentCell(selectedLine.row(), selectedLine.column())
        else:
            if stackType == "deck":
                connector.removeCardFromDeck(stackName, selectedCard["id"])
                deck = connector.getDeck(stackName)
                if deck is not None:
                    self.setCardList(deck["cardList"])
            elif stackType == "collection":
                connector.removeCardFromCollection(stackName, selectedCard["id"])
                collection = connector.getCollection(stackName)
                if collection is not None:
                    self.setCardList(collection["cardList"])
            else:
                ...
        self.parent().parent().parent().sort()  # type: ignore[union-attr]

    def addQty(self, qty: int):
        selectedLine = self.selectedIndexes()[0]
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.ItemDataRole.UserRole)["data"]
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.changeCardDeckQty(stackName, selectedCard["qty"] + qty, selectedCard["id"])
            deck = connector.getDeck(stackName)
            if deck is not None:
                self.setCardList(deck["cardList"])
        elif stackType == "collection":
            connector.changeCardCollectionQty(stackName, selectedCard["qty"] + qty, selectedCard["id"])
            collection = connector.getCollection(stackName)
            if collection is not None:
                self.setCardList(collection["cardList"])
        else:
            ...
        self.setCurrentCell(selectedLine.row(), selectedLine.column())

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Minus:
            self.removeQty(qty=1)
        elif event.key() == QtCore.Qt.Key.Key_Plus:
            self.addQty(qty=1)
        else:
            return super().keyPressEvent(event)

    def replaceCardInStack(self, oldCardId: str, newCardId: str):
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.replaceCardInDeck(stackName, oldCardId, newCardId)
            deck = connector.getDeck(stackName)
            if deck is not None:
                self.setCardList(deck["cardList"])
        elif stackType == "collection":
            connector.replaceCardInCollection(stackName, oldCardId, newCardId)
            collection = connector.getCollection(stackName)
            if collection is not None:
                self.setCardList(collection["cardList"])

    def updateCardListInfos(self):
        _loadingBar = qt.findAttrInParents(self, 'deckLoadingBar')
        if _loadingBar is not None:
            _loadingBar.setVisible(False)
        self._updateStatsPanel(self.cardStack)
        self.resizeColumnsToContents()

    def _updateStatsPanel(self, cardsList: list) -> None:
        manaValues = [0, 0, 0, 0, 0, 0, 0]  # 0, 1, 2, 3, 4, 5, 6+
        cardCount = 0
        totalPrice = 0
        colorPie = {}
        typePie = {}
        legalities = {}
        if len(cardsList) > 0:
            for _format in cardsList[0][1]["legalities"].keys():
                legalities.update({_format: "legal"})

        totalCmc = 0
        for qty, card in cardsList:
            if isinstance(qty, str):  # backward compatible hack
                qty = int(qty)
            isNotLand = not card["type_line"].startswith("Land") and not card["type_line"].startswith("Basic Land")
            isNotToken = "Token" not in card["type_line"]
            if isNotLand and isNotToken:
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
            if isNotToken:
                # cardCount
                cardCount += qty
            # cardPrice
            cardPrice = utils.getFromDict(card, ["prices", constants.CURRENCY[0]])
            if cardPrice is not None:
                totalPrice += qty * float(cardPrice)
            # typePie
            if isNotToken:
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
                        continue  # skip unknown legality types gracefully
                    elif format in legalities.keys():
                        # TODO handle "restricted"
                        if legality == "legal" and card["legalities"][format] == "legal":
                            ...
                        elif card["legalities"][format] == "restricted":
                            if format == "paupercommander":
                                # ! Can only be commander
                                ...
                            else:
                                if qty == 1:
                                    ...
                                else:
                                    legalities[format] = "not_legal"
                        else:
                            legalities[format] = "not_legal"
                    else:
                        legalities.update({format: legality})

        updateDict = {
            "manaValues": manaValues,
            "cardCount": cardCount,
            "totalCmc": totalCmc,
            "totalPrice": totalPrice,
            "colorPie": colorPie,
            "typePie": typePie,
            "legalities": legalities
        }
        qt.findAttrInParents(self, "decklist").infoPanel.updateValues(updateDict)

    def setCards(self, cardsList: list):
        self.setRowCount(0)
        for qty, card in cardsList:
            self.insertRow(self.rowCount())
            if isinstance(qty, str):  # backward compatible hack
                qty = int(qty)
            card.update({"qty": qty})
            self._addOneLine(card)
        self._updateStatsPanel(cardsList)
        self.resizeColumnsToContents()
