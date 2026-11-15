from PySide6 import QtWidgets, QtCore, QtGui
import logging
import traceback

from lib import scryfall, qt
from widgets.cardlistwidget import CardSearchListWidget
import constants


class SearchWorker(QtCore.QObject):
    finished = QtCore.Signal(int, list, bool)
    failed = QtCore.Signal(int, str)

    def __init__(self, requestId: int, searchDict: dict, limit: int):
        super().__init__()
        self._requestId = requestId
        self._searchDict = searchDict
        self._limit = limit

    def run(self):
        try:
            cards, truncated = scryfall.searchCardsLimited(self._searchDict, self._limit)
        except Exception:
            logging.exception("Card search failed")
            self.failed.emit(self._requestId, traceback.format_exc())
        else:
            self.finished.emit(self._requestId, cards, truncated)


class DbBrowser(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # To Build
    def __init__(self, parent=None, **kwargs):
        super(DbBrowser, self).__init__(parent=parent, **kwargs)

        self._searchThread: QtCore.QThread | None = None
        self._searchWorker: SearchWorker | None = None
        self._searchRequestId = 0
        self._searchLabel = ""
        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        self.mainLayout.addWidget(self.splitter)

        self.searchForm = SearchForm(parent=self)
        # self.searchForm.setMaximumWidth(300)
        self.searchForm.setMinimumWidth(300)
        self.searchForm.searched.connect(self.on_searchRequest)
        self.searchForm.cleared.connect(self.on_searchCleared)
        self.qscroll = QtWidgets.QScrollArea()
        self.qscroll.setWidgetResizable(True)
        self.qscroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.qscroll.setWidget(self.searchForm)

        self.searchPanel = QtWidgets.QWidget()
        self.searchPanelLayout = QtWidgets.QVBoxLayout(self.searchPanel)
        self.searchPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.searchPanelLayout.addWidget(self.qscroll, 1)

        self.searchButtonsWidget = QtWidgets.QWidget()
        self.searchButtonsLayout = QtWidgets.QHBoxLayout(self.searchButtonsWidget)
        self.searchButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.searchButton = QtWidgets.QPushButton("Search")
        self.searchButton.clicked.connect(self.searchForm.on_searchAction)
        self.searchButtonsLayout.addWidget(self.searchButton)
        self.clearButton = QtWidgets.QPushButton("Clear")
        self.clearButton.clicked.connect(self.searchForm.clearSearch)
        self.searchButtonsLayout.addWidget(self.clearButton)
        self.searchPanelLayout.addWidget(self.searchButtonsWidget)
        self.splitter.addWidget(self.searchPanel)
        # Results table with an optional truncation notice
        self.resultsWidget = QtWidgets.QWidget()
        self.resultsLayout = QtWidgets.QVBoxLayout(self.resultsWidget)
        self.resultsInfoLabel = QtWidgets.QLabel("")
        self.resultsInfoLabel.setWordWrap(True)
        self.resultsInfoLabel.setVisible(False)
        self.resultsLayout.addWidget(self.resultsInfoLabel)
        self.dbResultsList = CardSearchListWidget()
        self.dbResultsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.resultsLayout.addWidget(self.dbResultsList)
        self.splitter.addWidget(self.resultsWidget)
        self.splitter.setSizes([300, 600])

    @staticmethod
    def _logSearchRequest(searchDict: dict):
        logging.info(f"Search request: {searchDict}")

    def on_searchCleared(self):
        self._searchRequestId += 1
        self.dbResultsList.setCards([])
        self.resultsInfoLabel.clear()
        self.resultsInfoLabel.setVisible(False)
        logging.info("Search cleared")

    def on_searchRequest(self, searchDict: dict):
        self._logSearchRequest(searchDict)
        if self._searchThread is not None and self._searchThread.isRunning():
            logging.info("A search is already running")
            return
        self._searchRequestId += 1
        self._searchLabel = searchDict.get("name") or "selected filters"
        logging.info(f"Searching for {self._searchLabel}...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)

        self._searchThread = QtCore.QThread(self)
        self._searchWorker = SearchWorker(
            self._searchRequestId,
            searchDict,
            constants.SEARCH_RESULT_LIMIT,
        )
        self._searchWorker.moveToThread(self._searchThread)
        self._searchThread.started.connect(self._searchWorker.run)
        self._searchWorker.finished.connect(self._on_searchFinished)
        self._searchWorker.failed.connect(self._on_searchFailed)
        self._searchWorker.finished.connect(self._searchThread.quit)
        self._searchWorker.failed.connect(self._searchThread.quit)
        self._searchWorker.finished.connect(self._searchWorker.deleteLater)
        self._searchWorker.failed.connect(self._searchWorker.deleteLater)
        self._searchThread.finished.connect(self._on_searchThreadFinished)
        self._searchThread.start()

    def _on_searchFinished(self, requestId: int, cards: list, truncated: bool):
        if requestId != self._searchRequestId:
            return
        self._applySearchResults(cards, self._searchLabel, truncated)

    def _on_searchFailed(self, requestId: int, error: str):
        if requestId != self._searchRequestId:
            return
        logging.error(f"Search failed: {error}")

    def _on_searchThreadFinished(self):
        QtWidgets.QApplication.restoreOverrideCursor()
        if self._searchThread is not None:
            self._searchThread.deleteLater()
        self._searchThread = None
        self._searchWorker = None

    def _applySearchResults(self, cards: list, searchLabel: str, truncated: bool = False):
        if not cards:
            logging.info(f"No cards found for search {searchLabel!r}")
        elif truncated:
            logging.info(
                f"Showing the first {len(cards)} results; more cards match"
            )
        else:
            logging.info(f"Search returned {len(cards)} cards")
        self.resultsInfoLabel.setVisible(truncated)
        if truncated:
            self.resultsInfoLabel.setText(
                f"Showing the first {len(cards)} results; more cards match. Refine your search."
            )
        cardList = [(1, card) for card in cards]
        self.dbResultsList.setCards(cardList)

    def on_dbSelectChanged(self):
        if len(self.dbResultsList.selectedItems()) == 1:
            selectedItem = self.dbResultsList.selectedItems()[0]
            self.cardSelected.emit(selectedItem.data(QtCore.Qt.ItemDataRole.UserRole)["data"]["id"])
        else:
            selectedItem = None


class SearchForm(QtWidgets.QWidget):

    searched: QtCore.Signal = QtCore.Signal(dict)   # ? replace with search dict object ?
    cleared: QtCore.Signal = QtCore.Signal()

    # To Build
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.mainLayout = QtWidgets.QFormLayout()
        self.setLayout(self.mainLayout)

        self.nameField = QtWidgets.QLineEdit()
        self.nameField.returnPressed.connect(self.on_searchAction)
        self.mainLayout.addRow("Name", self.nameField)

        self.langCB = qt.NoWheelComboBox()
        for langName in constants.LANGS.values():
            self.langCB.addItem(langName)
        self.langCB.setCurrentText(list(constants.LANGS.values())[0])
        self.mainLayout.addRow("Lang", self.langCB)

        self.manaColorSelectorWidget = ManaColorSelectorWidget(parent=self)
        self.mainLayout.addRow("Colors", self.manaColorSelectorWidget)

        self.typeCB = qt.NoWheelComboBox()
        self.typeCB.addItem("")
        for cardType in constants.MAIN_CARD_TYPES:
            self.typeCB.addItem(cardType)
        self.typeCB.setCurrentText("")
        self.typeCB.currentTextChanged.connect(self.on_mainTypeChange)
        self.mainLayout.addRow("Main type", self.typeCB)

        self.otherTypeCB = QtWidgets.QLineEdit()
        self.otherTypeCB.returnPressed.connect(self.on_searchAction)
        self.otherTypeCB.setToolTip("Free input types/subtypes separated by spaces")
        self.mainLayout.addRow("Other type(s)", self.otherTypeCB)

        self.oracleTextLE = QtWidgets.QLineEdit()
        self.oracleTextLE.returnPressed.connect(self.on_searchAction)
        self.mainLayout.addRow("Oracle text", self.oracleTextLE)

        self.cmcWidget = QtWidgets.QWidget()
        self.cmcWidgetLayout = QtWidgets.QHBoxLayout()
        self.cmcWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.cmcWidget.setLayout(self.cmcWidgetLayout)
        self.cmcWidgetCB = qt.NoWheelComboBox()
        self.cmcWidgetCB.addItems(["=", ">", "<"])
        self.cmcWidgetCB.setMinimumWidth(64)
        self.cmcWidgetLayout.addWidget(self.cmcWidgetCB)
        self.cmcWidgetValue = QtWidgets.QLineEdit()
        self.cmcWidgetValue.setValidator(QtGui.QIntValidator(0, 15))
        self.cmcWidgetValue.returnPressed.connect(self.on_searchAction)
        self.cmcWidgetLayout.addWidget(self.cmcWidgetValue)
        self.mainLayout.addRow("CMC", self.cmcWidget)

        self.rarityCB = qt.NoWheelComboBox()
        self.rarityCB.addItems(["", "common", "uncommon", "rare", "mythic"])
        self.mainLayout.addRow("Rarity", self.rarityCB)

        self.setSelectorWidget = qt.ExtendedComboBox()
        self.mainLayout.addRow("Set", self.setSelectorWidget)

        self.formatLegalWidget = qt.ExtendedComboBox()
        self.mainLayout.addRow("Legality", self.formatLegalWidget)

        self.creaturePowerWidget = QtWidgets.QWidget()
        self.creaturePowerWidgetLayout = QtWidgets.QHBoxLayout()
        self.creaturePowerWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.creaturePowerWidget.setLayout(self.creaturePowerWidgetLayout)
        self.creaturePowerWidgetCB = qt.NoWheelComboBox()
        self.creaturePowerWidgetCB.setMinimumWidth(64)
        self.creaturePowerWidgetCB.addItems(["<", "=", ">"])
        self.creaturePowerWidgetLayout.addWidget(self.creaturePowerWidgetCB)
        self.creaturePowerWidgetLE = QtWidgets.QLineEdit()
        self.creaturePowerWidgetLE.setValidator(QtGui.QIntValidator(0, 20))
        self.creaturePowerWidgetLE.returnPressed.connect(self.on_searchAction)
        self.creaturePowerWidgetLayout.addWidget(self.creaturePowerWidgetLE)
        self.mainLayout.addRow("Power", self.creaturePowerWidget)
        self.creaturePowerRow = self.mainLayout.rowCount() - 1

        self.creatureToughnessWidget = QtWidgets.QWidget()
        self.creatureToughnessWidgetLayout = QtWidgets.QHBoxLayout()
        self.creatureToughnessWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.creatureToughnessWidget.setLayout(self.creatureToughnessWidgetLayout)
        self.creatureToughnessWidgetCB = qt.NoWheelComboBox()
        self.creatureToughnessWidgetCB.setMinimumWidth(64)
        self.creatureToughnessWidgetCB.addItems(["<", "=", ">"])
        self.creatureToughnessWidgetLayout.addWidget(self.creatureToughnessWidgetCB)
        self.creatureToughnessWidgetLE = QtWidgets.QLineEdit()
        self.creatureToughnessWidgetLE.setValidator(QtGui.QIntValidator(0, 20))
        self.creatureToughnessWidgetLE.returnPressed.connect(self.on_searchAction)
        self.creatureToughnessWidgetLayout.addWidget(self.creatureToughnessWidgetLE)
        self.mainLayout.addRow("Toughness", self.creatureToughnessWidget)
        self.creatureToughnessRow = self.mainLayout.rowCount() - 1

        self.planeswalkerLoyaltyWidget = QtWidgets.QWidget()
        self.planeswalkerLoyaltyWidgetLayout = QtWidgets.QHBoxLayout()
        self.planeswalkerLoyaltyWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.planeswalkerLoyaltyWidget.setLayout(self.planeswalkerLoyaltyWidgetLayout)
        self.planeswalkerLoyaltyWidgetCB = qt.NoWheelComboBox()
        self.planeswalkerLoyaltyWidgetCB.setMinimumWidth(64)
        self.planeswalkerLoyaltyWidgetCB.addItems(["<", "=", ">"])
        self.planeswalkerLoyaltyWidgetLayout.addWidget(self.planeswalkerLoyaltyWidgetCB)
        self.planeswalkerLoyaltyWidgetLE = QtWidgets.QLineEdit()
        self.planeswalkerLoyaltyWidgetLE.setValidator(QtGui.QIntValidator(0, 20))
        self.planeswalkerLoyaltyWidgetLE.returnPressed.connect(self.on_searchAction)
        self.planeswalkerLoyaltyWidgetLayout.addWidget(self.planeswalkerLoyaltyWidgetLE)
        self.mainLayout.addRow("Loyalty", self.planeswalkerLoyaltyWidget)
        self.planeswalkerLoyaltyRow = self.mainLayout.rowCount() - 1

        self.priceWidget = QtWidgets.QWidget()
        self.priceWidgetLayout = QtWidgets.QHBoxLayout()
        self.priceWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.priceWidget.setLayout(self.priceWidgetLayout)
        self.priceWidgetCB = qt.NoWheelComboBox()
        self.priceWidgetCB.setMinimumWidth(64)
        self.priceWidgetCB.addItems(["<", ">"])
        self.priceWidgetLayout.addWidget(self.priceWidgetCB)
        self.priceWidgetValue = QtWidgets.QLineEdit()
        self.priceWidgetValue.returnPressed.connect(self.on_searchAction)
        validator = QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"\d+(\.(\d)+)*"))
        self.priceWidgetValue.setValidator(validator)
        self.priceWidgetLayout.addWidget(self.priceWidgetValue)
        self.mainLayout.addRow("Price (" + constants.CURRENCY[1] + ")", self.priceWidget)

        # TODO check scryfall connection before (or switch to offline mode)
        atags, otags = scryfall.getTaggerTags()
        self.atagECB = qt.ExtendedComboBox()
        self.atagECB.addItems(atags)
        self.atagECB.setCurrentText("")
        self.atagECB.setToolTip("From scyfall Tagger community project")
        self.mainLayout.addRow("Art tag", self.atagECB)
        self.otagECB = qt.ExtendedComboBox()
        self.otagECB.addItems(otags)
        self.otagECB.setCurrentText("")
        self.otagECB.setToolTip("From scyfall Tagger community project")
        self.mainLayout.addRow("Oracle tag", self.otagECB)

        self.extrasCB = QtWidgets.QCheckBox("Include Extras")
        self.mainLayout.addRow("Extras", self.extrasCB)

        self.paperCB = QtWidgets.QCheckBox("Game: Paper")
        self.paperCB.setChecked(True)
        self.mainLayout.addRow("Paper only", self.paperCB)

        self.updateBulkModeControls()
        self._searchFields = [
            self.nameField,
            self.otherTypeCB,
            self.oracleTextLE,
            self.cmcWidgetValue,
            self.creaturePowerWidgetLE,
            self.creatureToughnessWidgetLE,
            self.planeswalkerLoyaltyWidgetLE,
            self.priceWidgetValue,
        ]
        for combo in (self.setSelectorWidget, self.formatLegalWidget, self.atagECB, self.otagECB):
            if combo.lineEdit() is not None:
                self._searchFields.append(combo.lineEdit())
        for field in self._searchFields:
            field.installEventFilter(self)
        self.refreshDataSources()
        self.on_mainTypeChange()

    def updateBulkModeControls(self):
        if constants.USE_BULK_FILES:
            self.extrasCB.setChecked(False)
            self.extrasCB.setEnabled(False)
            self.extrasCB.setToolTip("Extra-card filtering is not available in offline bulk mode")
        else:
            self.extrasCB.setEnabled(True)
            self.extrasCB.setToolTip("")

    def eventFilter(self, obj, event):
        if (
            event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter)
        ):
            self.on_searchAction()
            return True
        return super().eventFilter(obj, event)

    def refreshDataSources(self):
        self.updateBulkModeControls()
        currentSet = self.setSelectorWidget.currentText()
        currentFormat = self.formatLegalWidget.currentText()
        self.setSelectorWidget.clear()
        try:
            for set in scryfall.getSets():
                setYear = scryfall.getSetReleaseYear(set["id"])
                text = f"{set['name']} ({set['code'].upper()}) - {setYear}"
                self.setSelectorWidget.addItem(text)
        except Exception as e:
            logging.error(f"Could not load sets: {e}")
        self.setSelectorWidget.addItem("")
        self.setSelectorWidget.setCurrentText(currentSet)
        self.formatLegalWidget.clear()
        try:
            self.formatLegalWidget.addItems(scryfall.getFormats())
        except Exception as e:
            logging.error(f"Could not load formats: {e}")
        self.formatLegalWidget.addItem("")
        self.formatLegalWidget.setCurrentText(currentFormat)

    def on_searchAction(self):
        self.searched.emit(self.getSearchData())

    def clearSearch(self):
        self.nameField.clear()
        self.langCB.setCurrentIndex(0)
        self.manaColorSelectorWidget.reset()
        self.typeCB.setCurrentText("")
        self.otherTypeCB.clear()
        self.oracleTextLE.clear()
        self.cmcWidgetCB.setCurrentText("=")
        self.cmcWidgetValue.clear()
        self.rarityCB.setCurrentText("")
        self.setSelectorWidget.setCurrentText("")
        self.formatLegalWidget.setCurrentText("")
        self.creaturePowerWidgetCB.setCurrentText("<")
        self.creaturePowerWidgetLE.clear()
        self.creatureToughnessWidgetCB.setCurrentText("<")
        self.creatureToughnessWidgetLE.clear()
        self.planeswalkerLoyaltyWidgetCB.setCurrentText("<")
        self.planeswalkerLoyaltyWidgetLE.clear()
        self.priceWidgetCB.setCurrentText("<")
        self.priceWidgetValue.clear()
        self.atagECB.setCurrentText("")
        self.otagECB.setCurrentText("")
        self.extrasCB.setChecked(False)
        self.paperCB.setChecked(True)
        self.on_mainTypeChange()
        self.cleared.emit()

    def on_mainTypeChange(self):
        # TODO setRowVisible() only available on lates pyside6 versions
        if self.typeCB.currentText() == "creature":
            self.mainLayout.setRowVisible(self.creaturePowerRow, True)
            self.mainLayout.setRowVisible(self.creatureToughnessRow, True)
            self.mainLayout.setRowVisible(self.planeswalkerLoyaltyRow, False)
            self.planeswalkerLoyaltyWidgetLE.setText("")
        elif self.typeCB.currentText() == "planeswalker":
            self.mainLayout.setRowVisible(self.creaturePowerRow, False)
            self.creaturePowerWidgetLE.setText("")
            self.mainLayout.setRowVisible(self.creatureToughnessRow, False)
            self.creatureToughnessWidgetLE.setText("")
            self.mainLayout.setRowVisible(self.planeswalkerLoyaltyRow, True)
        else:
            self.mainLayout.setRowVisible(self.creaturePowerRow, False)
            self.creaturePowerWidgetLE.setText("")
            self.mainLayout.setRowVisible(self.creatureToughnessRow, False)
            self.creatureToughnessWidgetLE.setText("")
            self.mainLayout.setRowVisible(self.planeswalkerLoyaltyRow, False)
            self.planeswalkerLoyaltyWidgetLE.setText("")

    def getSearchData(self):
        langName = self.langCB.currentText()
        langCode = list(constants.LANGS.keys())[list(constants.LANGS.values()).index(langName)]
        colors = self.manaColorSelectorWidget.get()
        setText = self.setSelectorWidget.currentText()
        if "(" and ")" in setText:
            set = setText.split("(")[1].split(")")[0]
        else:
            set = ""
        if self.priceWidgetValue.text() != "":
            price = constants.CURRENCY[0] + self.priceWidgetCB.currentText() + self.priceWidgetValue.text()
        else:
            price = None
        searchData = {
            "name": self.nameField.text(),
            "include_extras": self.extrasCB.isChecked(),
            "lang": langCode,
            "colors": colors,
            "types": [self.typeCB.currentText()] + self.otherTypeCB.text().split(" "),
            "oracle": self.oracleTextLE.text(),  # TODO handle regex search
            "cmc": (self.cmcWidgetCB.currentText(), self.cmcWidgetValue.text()),
            "rarity": self.rarityCB.currentText(),
            "in": set,
            "price": price,
            "atag": self.atagECB.currentText(),
            "otag": self.otagECB.currentText(),
            "f": self.formatLegalWidget.currentText(),
        }

        if self.paperCB.isChecked():
            searchData.update({"game": "paper"})

        if self.typeCB.currentText() == "creature":
            if self.creaturePowerWidgetLE.text() != "":
                searchData.update(
                    {"pow": self.creaturePowerWidgetCB.currentText() + self.creaturePowerWidgetLE.text()})
            if self.creatureToughnessWidgetLE.text() != "":
                searchData.update(
                    {"tou": self.creatureToughnessWidgetCB.currentText() + self.creatureToughnessWidgetLE.text()})
        elif self.typeCB.currentText() == "planeswalker":
            if self.planeswalkerLoyaltyWidgetLE.text() != "":
                searchData.update(
                    {"loy": self.planeswalkerLoyaltyWidgetCB.currentText() + self.planeswalkerLoyaltyWidgetLE.text()}
                )
        else:
            ...

        return searchData


class ManaColorSelectorWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.colorManaWidgets = {}
        for color in "WUBRG":
            self.colorManaWidgets.update({color: ManaColorWidget(color, parent=self)})
        for colorWidget in self.colorManaWidgets.values():
            self.mainLayout.addWidget(colorWidget)

    def reset(self):
        for widget in self.colorManaWidgets.values():
            widget.state = "NS"
            widget.draw()

    def get(self) -> str:
        exclude = ""
        colors = ""
        for color, widget in self.colorManaWidgets.items():
            if widget.state == "Not":
                exclude += color
            elif widget.state != "NS":
                colors += color
        text = ""
        if colors != "":
            text += f"c:{colors.lower()}"
        if exclude != "":
            for color in exclude:
                text += f" -c:{color.lower()}"

        return text


class ManaColorWidget(QtWidgets.QWidget):

    STATES = ["NS", "May", "Not"]
    # TODO : handle "must" contain

    TOOLTIPS = {
        "NS": "Not selected",
        "May": "May contain",
        "Must": "Must contain",
        "Not": "Doesn't contain"
    }

    HALF_MANA_EQU = {
        "W": "L",
        "U": "M",
        "B": "N",
        "R": "O",
        "G": "P",
    }

    def __init__(self, color: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.color = color
        self.mainLayout = QtWidgets.QHBoxLayout()
        # self.mainLayout = QtWidgets.QStackedLayout()  # If interesting to strike down mana symbol on "not" ?
        self.setLayout(self.mainLayout)
        self.state = self.STATES[0]
        self.manaSymbolLabel = QtWidgets.QLabel("")
        self.mainLayout.addWidget(self.manaSymbolLabel)
        self._labelFont = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
            qt.findAttrInParents(self, "proxyglyphFontId")))
        self._labelFont.setPointSize(16)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.draw()

    def draw(self):
        if self.state in ["NS", "May", "Must", "Not"]:
            text = self.color.lower()
            self.manaSymbolLabel.setText(text)
        else:  # May is half symbol  NOT USED
            text = self.HALF_MANA_EQU[self.color]
            self.manaSymbolLabel.setText(text)
        self.manaSymbolLabel.setFont(self._labelFont)

        if self.state in ["NS"]:
            self.manaSymbolLabel.setStyleSheet(
                "color: black; font-family: Proxyglyph; font: 32px")
        elif self.state in ["Not"]:
            self.manaSymbolLabel.setStyleSheet(
                "color: red; font-family: Proxyglyph; font: 32px")
        else:
            self.manaSymbolLabel.setStyleSheet(
                "font-family: Proxyglyph; font: 32px")
        self.setToolTip(self.TOOLTIPS[self.state])

    def mousePressEvent(self, event):
        previousStateIndex = self.STATES.index(self.state)
        if previousStateIndex >= len(self.STATES) - 1:
            self.state = self.STATES[0]
        else:
            self.state = self.STATES[previousStateIndex + 1]
        self.draw()
