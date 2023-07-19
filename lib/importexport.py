import re
from PySide6 import QtWidgets, QtGui
import logging
import csv
import io
import pyperclip
import lxml.etree

import constants

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

import connector  # noqa E402
from lib import utils, scryfall  # noqa E402


class importDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)

        self.setWindowTitle("Import tool")

        line = utils.counter()

        self.importLabel = QtWidgets.QLabel("Import source : ")
        self.mainLayout.addWidget(self.importLabel, line.postinc(), 0, 1, 3)

        self.fromClipboardPB = QtWidgets.QPushButton("from clipboard")
        self.fromClipboardPB.clicked.connect(self.on_fromClipboardPBClicked)
        self.mainLayout.addWidget(self.fromClipboardPB, line.val(), 0)
        self.fromfilePB = QtWidgets.QPushButton("from file")
        self.fromfilePB.setEnabled(False)  # Not implemented
        self.mainLayout.addWidget(self.fromfilePB, line.val(), 1)
        self.fromUrlPB = QtWidgets.QPushButton("from url")
        self.fromUrlPB.setEnabled(False)  # Not implemented
        self.mainLayout.addWidget(self.fromUrlPB, line.postinc(), 2)

        self.textEdit = QtWidgets.QPlainTextEdit()
        self.mainLayout.addWidget(self.textEdit, line.postinc(), 0, 1, 3)

        self.formatSelectGroup = QtWidgets.QGroupBox("Format Select")
        self.formatSelectLayout = QtWidgets.QVBoxLayout()
        self.formatSelectGroup.setLayout(self.formatSelectLayout)
        for importFormat in constants.IMPORT_FORMATS:
            _radioButton = QtWidgets.QRadioButton(importFormat)
            _radioButton.clicked.connect(self.checkInputImport)
            self.formatSelectLayout.addWidget(_radioButton)
        self.mainLayout.addWidget(self.formatSelectGroup, line.postinc(), 0, 1, 3)

        self.collectionChooser = QtWidgets.QComboBox()
        self.collectionChooser.addItems(["Deck", "Collection"])
        self.mainLayout.addWidget(self.collectionChooser, line.val(), 0, 1, 1)
        self.collectionNameLabel = QtWidgets.QLabel("Name :")
        self.mainLayout.addWidget(self.collectionNameLabel, line.val(), 1, 1, 1)
        self.collectionNameLE = QtWidgets.QLineEdit("")
        self.mainLayout.addWidget(self.collectionNameLE, line.postinc(), 2, 1, 1)

        self.autoSetCB = QtWidgets.QCheckBox("Automatically choose set (most recent) if not given")
        self.autoSetCB.setChecked(True)
        self.mainLayout.addWidget(self.autoSetCB, line.postinc(), 0, 3, 1)

        self.importButtonPB = QtWidgets.QPushButton("Import")
        self.importButtonPB.setEnabled(False)
        self.importButtonPB.clicked.connect(self.on_importPBclicked)
        self.mainLayout.addWidget(self.importButtonPB, line.postinc(), 1, 1, 1)

    def on_fromClipboardPBClicked(self):
        self.textEdit.setPlainText(pyperclip.paste())

    def on_importPBclicked(self):
        isValid, errorMsg = self.checkInputImport(autoset=self.autoSetCB.isChecked())
        if isValid:
            if self.importer is not None:
                self.importer.toDatabase(self.collectionNameLE.text())
            self.close()
        else:
            # TODO show error msg
            print(errorMsg)

    def getSelectedImportFormat(self) -> str:
        selectedFormat = None
        for i in range(self.formatSelectLayout.count()):
            radioButton = self.formatSelectLayout.itemAt(i).wid
            if radioButton.isChecked():
                selectedFormat = radioButton.text()
        return selectedFormat

    def checkInputImport(self, autoset: bool):
        format = self.getSelectedImportFormat()
        isValid = False
        errorMsg = ""
        if format == "MTGO .dek":
            self.importer = MTGO_DEK_importer(self)
            isValid, errorMsg = self.importer.loadInput(self.textEdit.toPlainText())
        elif format == "MTG Arena":
            self.importer = MTGA_importer(self)
            isValid, errorMsg = self.importer.loadInput(self.textEdit.toPlainText(), autoSet=autoset)
        elif format == "CSV":
            self.importer = CSV_importer(self)
            isValid, errorMsg = self.importer.loadInput(self.textEdit.toPlainText(), autoSet=autoset)
        else:
            raise NotImplementedError
        if isValid:
            self.importButtonPB.setEnabled(True)
        else:
            QtWidgets.QMessageBox.information(self, "Could not import", errorMsg)
            self.importButtonPB.setEnabled(False)
        return isValid, errorMsg


class SetChooserDialog(QtWidgets.QDialog):
    def __init__(self, cardName: str, sets: list[str], parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("Choose set")

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.buttonWidget = QtWidgets.QWidget()
        self.buttonLayout = QtWidgets.QGridLayout()
        self.buttonWidget.setLayout(self.buttonLayout)
        self.sets = sets
        self.resultSetIndex = None
        self.setButtons = []
        N_COLUMNS = 10

        # sort sets by year
        setsSortedList = []
        for setCode in sets:
            setYear = scryfall.getSetReleaseYear(scryfall.getSetDataByCode(setCode, 'id'))
            setsSortedList.append((setCode, setYear))
        setsSortedList.sort(key=lambda _: _[1])
        sets = [_[0] for _ in setsSortedList]

        for i, set in enumerate(sets):
            _button = QtWidgets.QPushButton()
            _button.setFont(
                QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                    self.parent().parent().parent().parent().parent().keyruneFontId)))
            _button.setStyleSheet("QPushButton{font-size: 20px;font-family: Keyrune; font-weight: normal}")
            _button.setText(utils.setSetsText([set]) + " " + set)
            _button.clicked.connect(self.onSetButtonPushed)
            self.buttonLayout.addWidget(_button, int(i/N_COLUMNS), i % N_COLUMNS)

        message = QtWidgets.QLabel(f"Which set the card {cardName} comes from ?")
        self.mainLayout.addWidget(message)
        self.mainLayout.addWidget(self.buttonWidget)

    def onSetButtonPushed(self):
        set = self.sender().text().split(" ")[-1]
        setIndex = self.sets.index(set)
        self.setResult(setIndex)
        self.done(setIndex)


class importer:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.deckList = []

    def toDatabase(self, deckName):
        if self.parent.collectionChooser.currentText() == "Deck":
            connector.createDeck(deckName, self.deckList)
        elif self.parent.collectionChooser.currentText() == "Collection":
            connector.createCollection(deckName, self.deckList)
        else:
            raise NotImplementedError


class MTGA_importer(importer):
    """
    Example deck :
        # Deck
        19 Plains
        4 Thalia, Guardian of Thraben
        4 Brutal Cathar
    """
    def loadInput(self, text, autoSet: bool = True) -> bool:
        isValid = True
        errorMsg = ""
        lines = text.split("\n")
        self.deckList = []
        for line in lines:
            if not line.startswith("#") and not line == "":
                matched = re.fullmatch(r"(\d+)\s(.*)", line)
                if matched is not None:
                    qty, cardName = matched.groups()
                    qty = int(qty)
                    cards = scryfall.searchCards({"name": cardName}, exact=True)
                    if len(cards) == 0:
                        isValid = False
                        errorMsg += f"\ncould not find {cardName=}"
                    elif len(cards) == 1:
                        sets = scryfall.getCardReprints(cards[0]["id"])
                        if len(sets) > 1 and not autoSet:
                            _dialog = SetChooserDialog(parent=self.parent, cardName=cardName, sets=sets)
                            i = _dialog.exec()
                            set = sets[i]
                            cardId = scryfall.getCardReprintId(cards[0]["id"], set)  # TODO handle lang ?
                            self.deckList.append(
                                [qty, cardId]
                            )
                        else:
                            self.deckList.append(
                                [qty, cards[0]["id"]]
                            )
                    else:
                        logging.error(f"found multiple matches for {cardName=}")
                        print(cards)
                        # ask user
                else:
                    errorMsg += f"\nError on line {line=}"
        return isValid, errorMsg


class CSV_importer(importer):
    """
    Import from Urza Gatherer
    """
    def loadInput(self, text, autoSet: bool = True) -> bool:
        ftext = io.StringIO(text)
        reader = csv.reader(ftext, delimiter=",")
        cards = []
        headerLine = None
        for i, row in enumerate(reader):
            # Skip header by looking at "name" in real columns names line
            if headerLine is None and "name" not in [_.lower() for _ in row]:
                next
            elif headerLine is None and "name" in [_.lower() for _ in row]:
                headerLine = i
                columns = row
            elif headerLine is not None:
                card = {}
                for i, v in enumerate(row):
                    card.update({columns[i]: v})
                cards.append(card)

        # Check if Scryfall ID is in the available keys (Urza gatherer)
        # Urza Gatherer : "Scryfall ID"
        scryFallIdDictKey = None
        if "Scryfall ID".lower() in [_.lower() for _ in cards[0].keys()]:
            scryFallIdDictKey = list(cards[0].keys())[[_.lower() for _ in cards[0].keys()].index("Scryfall ID".lower())]

        # Get qty/count key
        # Urza Gatherer : "Count"
        countDictKey = None
        for countTestKey in ["qty", "count", "quantity"]:
            try:
                countDictKey = list(cards[0].keys())[[_.lower() for _ in cards[0].keys()].index(countTestKey.lower())]
            except ValueError:
                ...

        self.deckList = []
        for card in cards:
            if scryFallIdDictKey is not None:
                if countDictKey is not None:
                    self.deckList.append([card[countDictKey], card[scryFallIdDictKey]])
                else:  # if no quantity is given, assume one of each
                    self.deckList.append([1, card[scryFallIdDictKey]])

        return True, ""  # TODO grab errors


class MTGO_DEK_importer(importer):
    """
    .dek "xml" format
    """
    def loadInput(self, text: str) -> bool:
        self.deckList = []
        xmlRoot = lxml.etree.fromstring(text.encode(encoding="utf-8"))
        for card in xmlRoot.findall("Cards"):
            qty = int(card.attrib["Quantity"])
            mtgoId = card.attrib["CatID"]
            card = scryfall.getCardByMTGOId(int(mtgoId))
            self.deckList.append(
                [qty, card["id"]]
            )
        return True, ""  # TODO grab errors