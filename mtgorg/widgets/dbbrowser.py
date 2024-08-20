from PySide6 import QtWidgets, QtCore, QtGui

from lib import scryfall, qt
from widgets.cardlistwidget import CardSearchListWidget
import constants


class DbBrowser(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # To Build
    def __init__(self, parent=None, **kwargs):
        super(DbBrowser, self).__init__(parent=parent, **kwargs)

        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        self.mainLayout.addWidget(self.splitter)

        self.searchForm = SearchForm(parent=self)
        # self.searchForm.setMaximumWidth(300)
        self.searchForm.setMinimumWidth(300)
        self.searchForm.find.connect(self.on_searchRequest)
        self.qscroll = QtWidgets.QScrollArea()
        self.qscroll.setWidgetResizable(True)
        self.qscroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.qscroll.setWidget(self.searchForm)
        self.splitter.addWidget(self.qscroll)
        # QListWidget on the right for results
        self.dbResultsList = CardSearchListWidget()
        self.dbResultsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.splitter.addWidget(self.dbResultsList)
        self.splitter.setSizes([300, 600])

    def on_searchRequest(self, searchDict: dict):
        req = scryfall.searchCards(searchDict)
        cardList = [(1, card) for card in req]
        self.dbResultsList.setCards(cardList)

    def on_dbSelectChanged(self):
        if len(self.dbResultsList.selectedItems()) == 1:
            selectedItem = self.dbResultsList.selectedItems()[0]
            self.cardSelected.emit(selectedItem.data(QtCore.Qt.UserRole)["data"]["id"])
        else:
            selectedItem = None


class SearchForm(QtWidgets.QWidget):

    find: QtCore.Signal = QtCore.Signal(dict)   # ? replace with search dict object ?

    # To Build
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.mainLayout = QtWidgets.QFormLayout()
        self.setLayout(self.mainLayout)

        self.nameField = QtWidgets.QLineEdit()
        self.nameField.returnPressed.connect(self.on_searchAction)
        self.mainLayout.addRow("Name", self.nameField)

        self.langCB = QtWidgets.QComboBox()
        for langName in constants.LANGS.values():
            self.langCB.addItem(langName)
        self.langCB.setCurrentText(list(constants.LANGS.values())[0])
        self.mainLayout.addRow("Lang", self.langCB)

        self.manaColorSelectorWidget = ManaColorSelectorWidget(parent=self)
        self.mainLayout.addRow("Colors", self.manaColorSelectorWidget)

        self.typeCB = QtWidgets.QComboBox()
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
        self.cmcWidgetCB = QtWidgets.QComboBox()
        self.cmcWidgetCB.addItems(["=", ">", "<"])
        self.cmcWidgetCB.setMinimumWidth(64)
        self.cmcWidgetLayout.addWidget(self.cmcWidgetCB)
        self.cmcWidgetValue = QtWidgets.QLineEdit()
        self.cmcWidgetValue.setValidator(QtGui.QIntValidator(0, 15))
        self.cmcWidgetLayout.addWidget(self.cmcWidgetValue)
        self.mainLayout.addRow("CMC", self.cmcWidget)

        self.rarityCB = QtWidgets.QComboBox()
        self.rarityCB.addItems(["", "common", "uncommon", "rare", "mythic"])
        self.mainLayout.addRow("Rarity", self.rarityCB)

        self.setSelectorWidget = qt.ExtendedComboBox()
        sets = scryfall.getSets()
        for set in sets:
            setYear = scryfall.getSetReleaseYear(set["id"])
            text = f"{set['name']} ({set['code'].upper()}) - {setYear}"
            self.setSelectorWidget.addItem(text)
        self.setSelectorWidget.addItem("")
        self.setSelectorWidget.setCurrentText("")
        self.mainLayout.addRow("Set", self.setSelectorWidget)

        self.formatLegalWidget = qt.ExtendedComboBox()
        self.formatLegalWidget.addItems(scryfall.getFormats())
        self.formatLegalWidget.addItem("")
        self.formatLegalWidget.setCurrentText("")
        self.mainLayout.addRow("Legality", self.formatLegalWidget)

        self.creaturePowerWidget = QtWidgets.QWidget()
        self.creaturePowerWidgetLayout = QtWidgets.QHBoxLayout()
        self.creaturePowerWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.creaturePowerWidget.setLayout(self.creaturePowerWidgetLayout)
        self.creaturePowerWidgetCB = QtWidgets.QComboBox()
        self.creaturePowerWidgetCB.setMinimumWidth(64)
        self.creaturePowerWidgetCB.addItems(["<", "=", ">"])
        self.creaturePowerWidgetLayout.addWidget(self.creaturePowerWidgetCB)
        self.creaturePowerWidgetLE = QtWidgets.QLineEdit()
        self.creaturePowerWidgetLE.setValidator(QtGui.QIntValidator(0, 20))
        self.creaturePowerWidgetLayout.addWidget(self.creaturePowerWidgetLE)
        self.mainLayout.addRow("Power", self.creaturePowerWidget)
        self.creaturePowerRow = self.mainLayout.rowCount() - 1

        self.creatureToughnessWidget = QtWidgets.QWidget()
        self.creatureToughnessWidgetLayout = QtWidgets.QHBoxLayout()
        self.creatureToughnessWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.creatureToughnessWidget.setLayout(self.creatureToughnessWidgetLayout)
        self.creatureToughnessWidgetCB = QtWidgets.QComboBox()
        self.creatureToughnessWidgetCB.setMinimumWidth(64)
        self.creatureToughnessWidgetCB.addItems(["<", "=", ">"])
        self.creatureToughnessWidgetLayout.addWidget(self.creatureToughnessWidgetCB)
        self.creatureToughnessWidgetLE = QtWidgets.QLineEdit()
        self.creatureToughnessWidgetLE.setValidator(QtGui.QIntValidator(0, 20))
        self.creatureToughnessWidgetLayout.addWidget(self.creatureToughnessWidgetLE)
        self.mainLayout.addRow("Toughness", self.creatureToughnessWidget)
        self.creatureToughnessRow = self.mainLayout.rowCount() - 1

        self.planeswalkerLoyaltyWidget = QtWidgets.QWidget()
        self.planeswalkerLoyaltyWidgetLayout = QtWidgets.QHBoxLayout()
        self.planeswalkerLoyaltyWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.planeswalkerLoyaltyWidget.setLayout(self.planeswalkerLoyaltyWidgetLayout)
        self.planeswalkerLoyaltyWidgetCB = QtWidgets.QComboBox()
        self.planeswalkerLoyaltyWidgetCB.setMinimumWidth(64)
        self.planeswalkerLoyaltyWidgetCB.addItems(["<", "=", ">"])
        self.planeswalkerLoyaltyWidgetLayout.addWidget(self.planeswalkerLoyaltyWidgetCB)
        self.planeswalkerLoyaltyWidgetLE = QtWidgets.QLineEdit()
        self.planeswalkerLoyaltyWidgetLE.setValidator(QtGui.QIntValidator(0, 20))
        self.planeswalkerLoyaltyWidgetLayout.addWidget(self.planeswalkerLoyaltyWidgetLE)
        self.mainLayout.addRow("Loyalty", self.planeswalkerLoyaltyWidget)
        self.planeswalkerLoyaltyRow = self.mainLayout.rowCount() - 1

        self.priceWidget = QtWidgets.QWidget()
        self.priceWidgetLayout = QtWidgets.QHBoxLayout()
        self.priceWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.priceWidget.setLayout(self.priceWidgetLayout)
        self.priceWidgetCB = QtWidgets.QComboBox()
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

        self.searchButton = QtWidgets.QPushButton("Search")
        self.searchButton.clicked.connect(self.on_searchAction)
        self.mainLayout.addRow(self.searchButton)

        self.on_mainTypeChange()

    def on_searchAction(self):
        self.find.emit(self.getSearchData())

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
            "oracle": self.oracleTextLE.text(),
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
            searchData.update(
                {
                    "pow": self.creaturePowerWidgetCB.currentText() + self.creaturePowerWidgetLE.text(),
                    "tou": self.creatureToughnessWidgetCB.currentText() + self.creatureToughnessWidgetLE.text(),
                }
            )
        elif self.typeCB.currentText() == "planeswalker":
            searchData.update(
                {"loy": self.planeswalkerLoyaltyWidgetCB.currentText() + self.planeswalkerLoyaltyWidgetLE.text()}
            )
        else:
            ...

        return searchData


class ManaColorSelectorWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.colorManaWidgets = {}
        for color in "WUBRG":
            self.colorManaWidgets.update({color: ManaColorWidget(color, parent=self)})
        for colorWidget in self.colorManaWidgets.values():
            self.mainLayout.addWidget(colorWidget)

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

    def __init__(self, color: str, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.color = color
        self.mainLayout = QtWidgets.QHBoxLayout()
        # self.mainLayout = QtWidgets.QStackedLayout()  # If interesting to strike down mana symbol on "not" ?
        self.setLayout(self.mainLayout)
        self.state = self.STATES[0]
        self.manaSymbolLabel = QtWidgets.QLabel("")
        self.mainLayout.addWidget(self.manaSymbolLabel)
        self.font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
            qt.findAttrInParents(self, "proxyglyphFontId")))
        self.font.setPointSize(16)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.draw()

    def draw(self):
        if self.state in ["NS", "May", "Must", "Not"]:
            text = self.color.lower()
            self.manaSymbolLabel.setText(text)
        else:  # May is half symbol  NOT USED
            text = self.HALF_MANA_EQU[self.color]
            self.manaSymbolLabel.setText(text)
        self.manaSymbolLabel.setFont(self.font)

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
