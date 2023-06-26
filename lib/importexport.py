import re
from PySide6 import QtWidgets

import constants

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

import connector  # noqa E402
from lib import scryfall  # noqa E402


class importDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)

        self.importLabel = QtWidgets.QLabel("Import source : ")
        self.mainLayout.addWidget(self.importLabel, 0, 0, 1, 3)

        self.fromClipboardPB = QtWidgets.QPushButton("from clipboard")
        self.mainLayout.addWidget(self.fromClipboardPB, 1, 0)
        self.fromfilePB = QtWidgets.QPushButton("from file")
        self.mainLayout.addWidget(self.fromfilePB, 1, 1)
        self.fromUrlPB = QtWidgets.QPushButton("from url")
        self.fromUrlPB.setEnabled(False)  # Not implemented
        self.mainLayout.addWidget(self.fromUrlPB, 1, 2)

        self.textEdit = QtWidgets.QPlainTextEdit()
        self.mainLayout.addWidget(self.textEdit, 2, 0, 1, 3)

        self.formatSelectGroup = QtWidgets.QGroupBox("Format Select")
        self.formatSelectLayout = QtWidgets.QVBoxLayout()
        self.formatSelectGroup.setLayout(self.formatSelectLayout)
        for importFormat in constants.IMPORT_FORMATS:
            _radioButton = QtWidgets.QRadioButton(importFormat)
            _radioButton.clicked.connect(self.checkInputImport)
            self.formatSelectLayout.addWidget(_radioButton)
        self.mainLayout.addWidget(self.formatSelectGroup, 3, 0, 1, 3)

        self.deckNameLabel = QtWidgets.QLabel("Deck Name :")
        self.mainLayout.addWidget(self.deckNameLabel, 4, 0, 1, 1)
        self.deckNameLE = QtWidgets.QLineEdit("")
        self.mainLayout.addWidget(self.deckNameLE, 4, 1, 1, 2)

        self.autoSetCB = QtWidgets.QCheckBox("Automatically choose set (most recent) if not given")
        self.autoSetCB.setChecked(True)
        self.mainLayout.addWidget(self.autoSetCB, 5, 0, 3, 1)

        self.importButtonPB = QtWidgets.QPushButton("Import deck")
        self.importButtonPB.setEnabled(False)
        self.importButtonPB.clicked.connect(self.on_importPBclicked)
        self.mainLayout.addWidget(self.importButtonPB, 6, 1, 1, 1)

    def on_importPBclicked(self):
        isValid, errorMsg = self.checkInputImport(autoset=self.autoSetCB.isChecked())
        if isValid:
            if self.importer is not None:
                self.importer.toDatabase(self.deckNameLE.text())
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
        if format == "MTGO":
            ...
        elif format == "MTG Arena":
            self.importer = MTGA_importer()
            isValid, errorMsg = self.importer.loadInputText(self.textEdit.toPlainText(), autoSet=autoset)
        else:
            raise NotImplementedError
        if isValid:
            self.importButtonPB.setEnabled(True)
        else:
            QtWidgets.QMessageBox.information(self, "Could not import", errorMsg)
            self.importButtonPB.setEnabled(False)
        return isValid, errorMsg


class MTGA_importer:
    """
    Example deck :
        # Deck
        19 Plains
        4 Thalia, Guardian of Thraben
        4 Brutal Cathar
    """

    def __init__(self) -> None:
        self.deckList = []

    def loadInputText(self, text, autoSet: bool = True) -> bool:
        isValid = True
        errorMsg = ""
        lines = text.split("\n")
        for line in lines:
            if not line.startswith("#"):
                matched = re.fullmatch(r"(\d+)\s(.*)", line)
                if matched is not None:
                    qty, cardName = matched.groups()
                    qty = int(qty)
                    cards = scryfall.searchCards({"name": cardName}, exact=True)  # https://scryfall.com/docs/syntax#exact
                    if len(cards) == 0:
                        isValid = False
                        errorMsg += f"\ncould not find {cardName=}"
                    elif len(cards) == 1:
                        sets = scryfall.getCardReprints(cards[0]["id"])
                        if len(sets) > 1 and not autoSet:
                            # TODO popup, ask set
                            print(sets)
                            ...
                        else:
                            self.deckList.append(
                                [qty, cards[0]["id"]]
                            )
                    else:
                        # Multiple or no cards found
                        print(cards)
                        # ask user
                else:
                    errorMsg += f"\nError on line {line=}"
        return isValid, errorMsg

    def toDatabase(self, deckName):
        connector.createDeck(deckName, self.deckList)


class MTGO_importer:
    """
    Example deck :
        Card Name,Quantity,ID #,Rarity,Set,Collector #,Premium,
        "Banisher Priest",1,51909,Uncommon,PRM,1136/1158,Yes'
        "Batterskull",10,51909,Uncommon,PRM,1136/1158,Yes'
    """

    def __init__(self) -> None:
        self.deckList = []

    def loadInputText(self, text) -> bool:
        ...

    def toDatabase(self):
        ...
