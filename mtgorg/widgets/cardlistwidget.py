from PySide6 import QtWidgets, QtCore, QtGui

import connector
from lib import deckrules, scryfall, utils, qt
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

SECTION_ORDER = ("commander", "main", "sideboard")

SECTION_LABELS = {
    "main": "Main",
    "sideboard": "Sideboard",
    "commander": "Commander",
}

COLUMN_MAX_WIDTHS = {
    "qty": 50,
    "name": 200,
    "mana_cost": 120,
    "type_line": 220,
    "set": 70,
    "sets": 120,
    "rarity": 80,
    "price": 100,
}


class CardSearchListWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, columns=COLUMNS) -> None:
        super().__init__(parent)
        self.columns = columns
        self.cardStack: list = []
        self.deckSection = "main"
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        # self.setSortingEnabled(True)  # TODO bugs on add/delete line ?
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)  # ? Not working with selection
        self.setHorizontalHeaderLabels(self.columns)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.horizontalHeader().setStretchLastSection(False)
        if self.columns:
            self.horizontalHeader().setSectionResizeMode(
                len(self.columns) - 1,
                QtWidgets.QHeaderView.ResizeMode.Interactive,
            )

    def resizeColumnsToContents(self):
        super().resizeColumnsToContents()
        for index, column in enumerate(self.columns):
            maxWidth = COLUMN_MAX_WIDTHS.get(column)
            if maxWidth is not None:
                self.setColumnWidth(index, min(self.columnWidth(index), maxWidth))
        self._stretchLastColumn()

    def _stretchLastColumn(self):
        if not self.columns:
            return
        last = len(self.columns) - 1
        available = self.viewport().width() - sum(self.columnWidth(i) for i in range(last))
        self.setColumnWidth(last, max(80, available))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._stretchLastColumn()

    def setDeckSection(self, section: str):
        self.deckSection = section

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
                    iconText = utils.setSetsText(text)
                    if iconText:
                        font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                            qt.findAttrInParents(self, "keyruneFontId")
                        ))
                        font.setPointSize(14)
                        item.setFont(font)
                        text = iconText
                    else:
                        text = " ".join(str(setCode).upper() for setCode in text)
                if column == "set" and "set" in cardData.keys():
                    iconText = utils.setSetsText([text])
                    if iconText:
                        font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                            qt.findAttrInParents(self, "keyruneFontId")
                        ))
                        font.setPointSize(14)
                        item.setFont(font)
                        text = iconText
                    else:
                        text = str(text).upper()
                if column == "price":
                    text = utils.getFromDict(cardData, ["prices", constants.CURRENCY[0]])
                    _foil_key = constants.CURRENCY[0] + "_foil"
                    if text is not None:
                        text = str(text) + " " + constants.CURRENCY[1]
                    elif utils.getFromDict(cardData, ["prices", _foil_key]) is not None:
                        foil_price = utils.getFromDict(cardData, ["prices", _foil_key])
                        text = f"{foil_price} {constants.CURRENCY[1]} (foil)"
                    else:
                        text = "N/A"
                item.setData(QtCore.Qt.ItemDataRole.DisplayRole, text)
                if column in ("name", "type_line") and isinstance(text, str):
                    item.setToolTip(text)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, {"data": cardData, "column": column})
                dataList.append(item)
        return dataList


class SectionsLoaderWorker(QtCore.QObject):
    finished = QtCore.Signal(int, dict)

    def __init__(self, requestId: int, sections: dict):
        super().__init__()
        self._requestId = requestId
        self._sections = sections

    def run(self):
        result = {}
        for section, entries in self._sections.items():
            cards = []
            for qty, cardId in entries:
                card = scryfall.getCardById(cardId)
                if card is not None:
                    cards.append((int(qty), card))
            result[section] = cards
        self.finished.emit(self._requestId, result)


class CardStackListWidget(CardSearchListWidget):
    cardListChanged = QtCore.Signal()

    # similar to the cardListWidget but whith specific data about qties, user comments, etc...
    def __init__(self, parent=None, columns=USER_COLUMNS, updateStats: bool = True) -> None:
        super().__init__(parent=parent, columns=columns)
        self.updateStats = updateStats
        self.sectionCardStacks: dict[str, list] = {}
        self.visibleSections = ["main"]
        self.showSectionHeaders = True
        self.rowSections: dict[int, str] = {}
        self.sectionHeaderRows: dict[str, int] = {}
        self.cardStack: list = []
        self.sortKey: str | None = None
        self._loadRequestId = 0
        self._loaderThread: QtCore.QThread | None = None
        self.setAcceptDrops(False)
        self.setDragEnabled(True)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_contextMenuRequested)
        self.setColumnCount(len(self.columns))
        self.verticalHeader().setVisible(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.setHorizontalHeaderLabels(self.columns)
        self.setMouseTracking(True)

    def on_contextMenuRequested(self, pos: QtCore.QPoint):
        row = self.rowAt(pos.y())
        section = self.rowSections.get(row)
        if section is None:
            return
        item = self.item(row, 0)
        if item is None:
            return
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType != "deck":
            return
        deck = connector.getDeck(stackName)
        if deck is None:
            return
        allowed = deckrules.allowedSections(deck.get("format", constants.DEFAULT_DECK_FORMAT))
        targets = [target for target in ("commander", "main", "sideboard") if target in allowed and target != section]
        if not targets:
            return
        self.selectRow(row)
        menu = QtWidgets.QMenu(self)
        for target in targets:
            action = menu.addAction(f"Move to {SECTION_LABELS[target]}")
            action.setData(target)
        chosen = menu.exec(self.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        self.moveCardToSection(row, chosen.data())

    def moveCardToSection(self, row: int, targetSection: str):
        section = self.rowSections.get(row)
        item = self.item(row, 0)
        if section is None or item is None:
            return
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType != "deck":
            return
        connector.moveCardInDeck(stackName, data["data"]["id"], section, targetSection)
        self.reloadFromDatabase()
        self.cardListChanged.emit()

    def on_itemChanged(self, item):
        if item.data(QtCore.Qt.ItemDataRole.UserRole) is None:
            return
        if item.data(QtCore.Qt.ItemDataRole.UserRole)["column"] != "qty":
            return
        previousQty = item.data(QtCore.Qt.ItemDataRole.UserRole)["data"]["qty"]
        try:
            newQty = int(item.text())
        except ValueError:
            item.setText(str(previousQty))
            return
        if newQty < 0:
            item.setText(str(previousQty))
            return
        if previousQty != newQty:
            if previousQty > newQty:
                self.removeQty(previousQty - newQty)
            else:
                self.addQty(newQty - previousQty)

    def setSections(self, sections: dict, visibleSections: set[str], showSectionHeaders: bool = True):
        self.visibleSections = [s for s in SECTION_ORDER if s in visibleSections]
        self.showSectionHeaders = showSectionHeaders
        self._loadRequestId += 1
        requestId = self._loadRequestId
        _loadingBar = qt.findAttrInParents(self, 'deckLoadingBar')
        if _loadingBar is not None:
            _loadingBar.setRange(0, 0)
            _loadingBar.setVisible(True)

        self._loaderThread = QtCore.QThread(self)
        self._loaderWorker = SectionsLoaderWorker(requestId, sections)
        self._loaderWorker.moveToThread(self._loaderThread)
        self._loaderThread.started.connect(self._loaderWorker.run)
        self._loaderWorker.finished.connect(self._on_sections_loaded)
        self._loaderWorker.finished.connect(self._loaderThread.quit)
        self._loaderWorker.finished.connect(self._loaderWorker.deleteLater)
        self._loaderThread.finished.connect(self._loaderThread.deleteLater)
        self._loaderThread.start()

    def setCardList(self, cardList):
        self.setSections({"main": cardList}, {"main"})

    def _on_sections_loaded(self, requestId: int, sections: dict):
        if requestId != self._loadRequestId:
            return
        self.sectionCardStacks = sections
        self.cardStack = sections.get("main", [])
        self._sortSectionLists()
        self.renderSections()
        _loadingBar = qt.findAttrInParents(self, 'deckLoadingBar')
        if _loadingBar is not None:
            _loadingBar.setVisible(False)
        if self.updateStats:
            self._updateStatsPanel(self.cardStack)

    def _sortSectionLists(self):
        if self.sortKey is None:
            return
        for cards in self.sectionCardStacks.values():
            if not cards:
                continue
            if self.sortKey == "prices":
                cards.sort(
                    key=lambda entry: float(
                        utils.getFromDict(
                            entry[1], ["prices", constants.CURRENCY[0]], 0
                        ) if utils.getFromDict(
                            entry[1], ["prices", constants.CURRENCY[0]], 0
                        ) is not None else 0
                    )
                )
            else:
                cards.sort(key=lambda entry: entry[1].get(self.sortKey, ""))

    def sortSections(self, key: str | None = None):
        if key is not None:
            self.sortKey = key
        self._sortSectionLists()
        self.renderSections()

    def renderSections(self):
        self.setRowCount(0)
        self.rowSections = {}
        self.sectionHeaderRows = {}
        for section in self.visibleSections:
            cards = self.sectionCardStacks.get(section, [])
            if self.showSectionHeaders:
                headerRow = self.rowCount()
                self.insertRow(headerRow)
                total = sum(qty for qty, _card in cards)
                header = QtWidgets.QTableWidgetItem(f"{SECTION_LABELS[section]} ({total})")
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                palette = self.palette()
                header.setBackground(palette.color(QtGui.QPalette.ColorRole.AlternateBase))
                header.setForeground(palette.color(QtGui.QPalette.ColorRole.Text))
                header.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                self.setItem(headerRow, 0, header)
                self.setSpan(headerRow, 0, 1, len(self.columns))
                self.sectionHeaderRows[section] = headerRow
            for qty, card in cards:
                row = self.rowCount()
                self.insertRow(row)
                card.update({"qty": qty})
                for columnIndex, item in enumerate(self.getCardTableItem(card, columns=self.columns)):
                    self.setItem(row, columnIndex, item)
                self.rowSections[row] = section
        self.resizeColumnsToContents()

    def _selectedSection(self) -> str:
        rows = {index.row() for index in self.selectedIndexes()}
        for row in rows:
            if row in self.rowSections:
                return self.rowSections[row]
        return "main"

    def reloadFromDatabase(self):
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            deck = connector.getDeck(stackName)
            if deck is None:
                return
            sections = {
                "main": deck.get("cardList", []),
                "sideboard": deck.get("sideboard", []),
                "commander": deck.get("commander", []),
            }
        elif stackType == "collection":
            collection = connector.getCollection(stackName)
            if collection is None:
                return
            sections = {"main": collection["cardList"]}
            self.visibleSections = ["main"]
            self.showSectionHeaders = False
        else:
            return
        self.setSections(sections, set(self.visibleSections), self.showSectionHeaders)

    def addCard(self, card: dict, section: str = "main"):
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.addCardToDeck(stackName, 1, card["id"], section=section)
        elif stackType == "collection":
            connector.addCardToCollection(stackName, 1, card["id"])
        else:
            return
        self.reloadFromDatabase()
        self.cardListChanged.emit()

    def removeQty(self, qty: int):
        if not self.selectedItems():
            return
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.ItemDataRole.UserRole)["data"]
        section = self._selectedSection()
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if selectedCard["qty"] > qty:
            if stackType == "deck":
                connector.changeCardDeckQty(
                    stackName, selectedCard["qty"] - qty, selectedCard["id"], section=section
                )
            elif stackType == "collection":
                connector.changeCardCollectionQty(stackName, selectedCard["qty"] - qty, selectedCard["id"])
        else:
            if stackType == "deck":
                connector.removeCardFromDeck(stackName, selectedCard["id"], section=section)
            elif stackType == "collection":
                connector.removeCardFromCollection(stackName, selectedCard["id"])
        self.reloadFromDatabase()
        self.cardListChanged.emit()

    def addQty(self, qty: int):
        if not self.selectedItems():
            return
        selectedCard = self.selectedItems()[0].data(QtCore.Qt.ItemDataRole.UserRole)["data"]
        section = self._selectedSection()
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.changeCardDeckQty(
                stackName, selectedCard["qty"] + qty, selectedCard["id"], section=section
            )
        elif stackType == "collection":
            connector.changeCardCollectionQty(stackName, selectedCard["qty"] + qty, selectedCard["id"])
        self.reloadFromDatabase()
        self.cardListChanged.emit()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Minus:
            self.removeQty(qty=1)
        elif event.key() == QtCore.Qt.Key.Key_Plus:
            self.addQty(qty=1)
        else:
            return super().keyPressEvent(event)

    def replaceCardInStack(self, oldCardId: str, newCardId: str):
        section = self._selectedSection()
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType == "deck":
            connector.replaceCardInDeck(stackName, oldCardId, newCardId, section=section)
        elif stackType == "collection":
            connector.replaceCardInCollection(stackName, oldCardId, newCardId)
        self.reloadFromDatabase()
        self.cardListChanged.emit()

    def updateCardListInfos(self):
        if self.updateStats:
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
