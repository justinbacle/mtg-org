from PySide6 import QtWidgets, QtCore, QtGui

import sys
import os

sys.path.append(os.getcwd())  # FIXME Remove

from lib import scryfall, qt, utils  # noqa E402
from widgets.cardlistwidget import CardListWidget  # noqa E402

import constants  # noqa E402


class DbBrowser(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # To Build
    def __init__(self, parent=None, **kwargs):
        super(DbBrowser, self).__init__(parent=parent, **kwargs)

        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)
        # Form on the left for search terms ?
        self.searchForm = SearchForm(parent=self)
        self.searchForm.setMaximumWidth(300)
        self.searchForm.find.connect(self.on_searchRequest)
        self.mainLayout.addWidget(self.searchForm)
        # QListWidget on the right for results
        self.dbResultsList = CardListWidget()
        self.dbResultsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.mainLayout.addWidget(self.dbResultsList)

    def on_searchRequest(self, searchDict: dict):
        req = scryfall.searchCards(searchDict)
        cardList = [(1, card) for card in req]
        self.dbResultsList.setCards(cardList)

    def on_dbSelectChanged(self):
        if len(self.dbResultsList.selectedItems()) == 1:
            selectedItem = self.dbResultsList.selectedItems()[0]
            self.cardSelected.emit(selectedItem.data(QtCore.Qt.UserRole)["id"])
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
        self.mainLayout.addRow("Main card type", self.typeCB)

        # TODO add free field for subtypes (-t:) to be merged with maintype

        self.oracleTextLE = QtWidgets.QLineEdit()
        self.oracleTextLE.returnPressed.connect(self.on_searchAction)
        self.mainLayout.addRow("Oracle text", self.oracleTextLE)

        self.cmcWidget = QtWidgets.QWidget()
        self.cmcWidgetLayout = QtWidgets.QHBoxLayout()
        self.cmcWidget.setLayout(self.cmcWidgetLayout)
        self.cmcWidgetCB = QtWidgets.QComboBox()
        self.cmcWidgetCB.addItems(["=", ">", "<"])
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
        # TODO add power/toughness/loyalty when creature / planeswalker is selected (pow/tou/loy)
        # TODO add format legality (f:)
        # TODO add min/max price filter
        # TODO add support for tagger tags (atag: / otag:)
        # TODO put in scrollable widget (QScrollArea)
        self.extrasCB = QtWidgets.QCheckBox("Include Extras")
        self.mainLayout.addRow("Extras", self.extrasCB)

        self.searchButton = QtWidgets.QPushButton("Search")
        self.searchButton.clicked.connect(self.on_searchAction)
        self.mainLayout.addRow(self.searchButton)

    def on_searchAction(self):
        self.find.emit(self.getSearchData())

    def getSearchData(self):
        langName = self.langCB.currentText()
        langCode = list(constants.LANGS.keys())[list(constants.LANGS.values()).index(langName)]
        colors = self.manaColorSelectorWidget.get()
        setText = self.setSelectorWidget.currentText()
        set = setText.split("(")[1].split(")")[0]
        searchData = {
            "name": self.nameField.text(),
            "include_extras": self.extrasCB.isChecked(),
            "lang": langCode,
            "colors": colors,
            "types": [self.typeCB.currentText()],
            "oracle": self.oracleTextLE.text(),
            "cmc": (self.cmcWidgetCB.currentText(), self.cmcWidgetValue.text()),
            "rarity": self.rarityCB.currentText(),
            "in": set,
        }
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
