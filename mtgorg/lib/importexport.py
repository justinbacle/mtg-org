import re
from PySide6 import QtWidgets, QtGui
import logging
import csv
import io
import pyperclip
import lxml.etree
import requests
from bs4 import BeautifulSoup
import urllib
from xml.sax.saxutils import escape

import constants
import connector
from lib import utils, scryfall, qt


def formatCardmarketExport(sections: dict, includeCommander: bool = True,
                           includeCompanion: bool = True, includeSideboard: bool = True,
                           discardSet: bool = False, cardLookup=None) -> str:
    """Return a flat Cardmarket wants-list decklist."""
    cardLookup = cardLookup or scryfall.getCardById
    sectionOrder = ["commander", "companion", "main", "sideboard"]
    include = {
        "main": True,
        "commander": includeCommander,
        "companion": includeCompanion,
        "sideboard": includeSideboard,
    }
    lines = []
    for section in sectionOrder:
        if not include.get(section, False):
            continue
        for qty, cardId in sections.get(section, []):
            card = cardLookup(cardId)
            if card is None:
                logging.warning(f"Could not export card {cardId}: not found")
                continue
            if discardSet:
                lines.append(f"{qty} {card['name']}")
            else:
                lines.append(f"{qty} {card['name']} ({card['set_name']})")
    return "\n".join(lines) + ("\n" if lines else "")


def formatMTGAExport(sections: dict, includeCommander: bool = True,
                     includeCompanion: bool = True, includeSideboard: bool = True,
                     cardLookup=None) -> str:
    cardLookup = cardLookup or scryfall.getCardById
    parts = []
    sectionHeaders = [
        ("main", "Deck", True),
        ("sideboard", "Sideboard", includeSideboard),
        ("commander", "Commander", includeCommander),
        ("companion", "Companion", includeCompanion),
    ]
    for section, header, included in sectionHeaders:
        if not included:
            continue
        entries = sections.get(section, [])
        if not entries:
            continue
        parts.append(header)
        for qty, cardId in entries:
            card = cardLookup(cardId)
            if card is None:
                logging.warning(f"Could not export card {cardId}: not found")
                continue
            parts.append(f"{qty} {card['name']}")
        parts.append("")
    return "\n".join(parts).rstrip() + ("\n" if parts else "")


def formatPlainTextExport(sections: dict, includeCommander: bool = True,
                          includeCompanion: bool = True, includeSideboard: bool = True,
                          discardSet: bool = False, cardLookup=None) -> str:
    cardLookup = cardLookup or scryfall.getCardById
    parts = []
    sectionHeaders = [
        ("commander", "Commander", includeCommander),
        ("companion", "Companion", includeCompanion),
        ("main", "Main", True),
        ("sideboard", "Sideboard", includeSideboard),
    ]
    for section, header, included in sectionHeaders:
        if not included:
            continue
        entries = sections.get(section, [])
        if not entries:
            continue
        parts.append(header)
        for qty, cardId in entries:
            card = cardLookup(cardId)
            if card is None:
                logging.warning(f"Could not export card {cardId}: not found")
                continue
            if discardSet:
                parts.append(f"{qty} {card['name']}")
            else:
                parts.append(f"{qty} {card['name']} ({card['set_name']})")
        parts.append("")
    return "\n".join(parts).rstrip() + ("\n" if parts else "")


def formatMTGOExport(sections: dict, includeCommander: bool = True,
                     includeCompanion: bool = True, includeSideboard: bool = True,
                     cardLookup=None) -> str:
    cardLookup = cardLookup or scryfall.getCardById
    cards = []

    def addSection(section: str, sideboard: bool):
        for qty, cardId in sections.get(section, []):
            card = cardLookup(cardId)
            if card is None:
                logging.warning(f"Could not export card {cardId}: not found")
                continue
            mtgoId = card.get("mtgo_id")
            if mtgoId is None:
                logging.warning(f"Card {card.get('name')} has no MTGO id; skipping")
                continue
            name = escape(card["name"], {'"': "&quot;"})
            cards.append(
                f'  <Cards CatID="{mtgoId}" Quantity="{qty}" '
                f'Sideboard="{str(sideboard).lower()}" Name="{name}" Annotation="0"/>'
            )

    addSection("main", False)
    if includeSideboard:
        addSection("sideboard", True)
    if includeCommander:
        if sections.get("commander"):
            logging.warning("MTGO .dek has no commander zone; exporting commander cards as main deck")
        addSection("commander", False)
    if includeCompanion:
        if sections.get("companion"):
            logging.warning("MTGO .dek has no companion zone; exporting companion cards to sideboard")
        addSection("companion", True)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Deck xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
        "  <NetDeckID>0</NetDeckID>",
        "  <PreconstructedDeckID>0</PreconstructedDeckID>",
        *cards,
        "</Deck>",
    ]
    return "\n".join(lines) + "\n"


class exportDialog(QtWidgets.QDialog):
    def __init__(self, sections: dict, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Export tool")

        self.sections = sections

        # Export type select
        self.exportTypeSelectorGB = QtWidgets.QGroupBox("Export type")
        self.exportTypeSelectorLayout = QtWidgets.QVBoxLayout()
        self.exportTypeSelectorGB.setLayout(self.exportTypeSelectorLayout)
        self.exportTypeSelector_cardmarketRB = QtWidgets.QRadioButton("Cardmarket")
        self.exportTypeSelector_mtgaRB = QtWidgets.QRadioButton("MTG Arena text")
        self.exportTypeSelector_mtgoRB = QtWidgets.QRadioButton("MTGO .dek")
        self.exportTypeSelector_plainRB = QtWidgets.QRadioButton("Plain text with sections")
        self.exportTypeSelectorGroup = QtWidgets.QButtonGroup(self)
        for radio in (
            self.exportTypeSelector_cardmarketRB,
            self.exportTypeSelector_mtgaRB,
            self.exportTypeSelector_mtgoRB,
            self.exportTypeSelector_plainRB,
        ):
            self.exportTypeSelectorGroup.addButton(radio)
            self.exportTypeSelectorLayout.addWidget(radio)
            radio.toggled.connect(self.on_typeSelectToggle)
        self.exportTypeSelector_cardmarketRB.setChecked(True)
        self.mainLayout.addWidget(self.exportTypeSelectorGB)

        # Sections to include
        self.sectionsGB = QtWidgets.QGroupBox("Sections")
        self.sectionsLayout = QtWidgets.QVBoxLayout()
        self.sectionsGB.setLayout(self.sectionsLayout)
        self.includeCommanderCB = QtWidgets.QCheckBox("Include commander")
        self.includeCompanionCB = QtWidgets.QCheckBox("Include companion")
        self.includeSideboardCB = QtWidgets.QCheckBox("Include sideboard")
        self.includeCommanderCB.setChecked(bool(self.sections.get("commander")))
        self.includeCompanionCB.setChecked(bool(self.sections.get("companion")))
        self.includeSideboardCB.setChecked(bool(self.sections.get("sideboard")))
        self.includeCommanderCB.setVisible(bool(self.sections.get("commander")))
        self.includeCompanionCB.setVisible(bool(self.sections.get("companion")))
        self.includeSideboardCB.setVisible(bool(self.sections.get("sideboard")))
        self.sectionsLayout.addWidget(self.includeCommanderCB)
        self.sectionsLayout.addWidget(self.includeCompanionCB)
        self.sectionsLayout.addWidget(self.includeSideboardCB)
        self.sectionsGB.setVisible(
            self.includeCommanderCB.isVisible()
            or self.includeCompanionCB.isVisible()
            or self.includeSideboardCB.isVisible()
        )
        self.mainLayout.addWidget(self.sectionsGB)

        # Options
        self.exportOptionsGB = QtWidgets.QGroupBox("Options")
        self.exportOptionsLayout = QtWidgets.QVBoxLayout()
        self.exportOptionsGB.setLayout(self.exportOptionsLayout)
        self.exportOptions_discardSetCB = QtWidgets.QCheckBox("Discard set info")
        self.exportOptionsLayout.addWidget(self.exportOptions_discardSetCB)
        self.mainLayout.addWidget(self.exportOptionsGB)

        # Destination
        self.destinationSelectorGB = QtWidgets.QGroupBox("Destination")
        self.destinationSelectorLayout = QtWidgets.QVBoxLayout()
        self.destinationSelectorGB.setLayout(self.destinationSelectorLayout)
        self.destinationSelect_ClipboardRB = QtWidgets.QRadioButton("Clipboard")
        self.destinationSelect_ClipboardRB.setChecked(True)
        self.destinationSelectorLayout.addWidget(self.destinationSelect_ClipboardRB)
        self.mainLayout.addWidget(self.destinationSelectorGB)

        # Ok button
        self.okButton = QtWidgets.QPushButton("OK")
        self.okButton.pressed.connect(self.on_okButtonPressed)
        self.mainLayout.addWidget(self.okButton)

    def on_typeSelectToggle(self):
        discardSetCapable = (
            self.exportTypeSelector_cardmarketRB.isChecked()
            or self.exportTypeSelector_plainRB.isChecked()
        )
        self.exportOptions_discardSetCB.setEnabled(discardSetCapable)

    def buildExportText(self) -> str:
        includeCommander = self.includeCommanderCB.isChecked()
        includeCompanion = self.includeCompanionCB.isChecked()
        includeSideboard = self.includeSideboardCB.isChecked()
        discardSet = self.exportOptions_discardSetCB.isChecked()
        if self.exportTypeSelector_cardmarketRB.isChecked():
            return formatCardmarketExport(
                self.sections,
                includeCommander=includeCommander,
                includeCompanion=includeCompanion,
                includeSideboard=includeSideboard,
                discardSet=discardSet,
            )
        if self.exportTypeSelector_mtgaRB.isChecked():
            return formatMTGAExport(
                self.sections,
                includeCommander=includeCommander,
                includeCompanion=includeCompanion,
                includeSideboard=includeSideboard,
            )
        if self.exportTypeSelector_mtgoRB.isChecked():
            return formatMTGOExport(
                self.sections,
                includeCommander=includeCommander,
                includeCompanion=includeCompanion,
                includeSideboard=includeSideboard,
            )
        if self.exportTypeSelector_plainRB.isChecked():
            return formatPlainTextExport(
                self.sections,
                includeCommander=includeCommander,
                includeCompanion=includeCompanion,
                includeSideboard=includeSideboard,
                discardSet=discardSet,
            )
        raise NotImplementedError

    def on_okButtonPressed(self):
        exportTxt = self.buildExportText()
        if self.destinationSelect_ClipboardRB.isChecked():
            pyperclip.copy(exportTxt)
        self.close()


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

        self.deckFormatLabel = QtWidgets.QLabel("Deck format:")
        self.mainLayout.addWidget(self.deckFormatLabel, line.val(), 0, 1, 1)
        self.deckFormatCB = qt.NoWheelComboBox()
        for key, info in constants.DECK_FORMATS.items():
            self.deckFormatCB.addItem(info["label"], key)
        self.mainLayout.addWidget(self.deckFormatCB, line.postinc(), 1, 1, 2)

        self.importButtonPB = QtWidgets.QPushButton("Import")
        self.importButtonPB.setEnabled(False)
        self.importButtonPB.clicked.connect(self.on_importPBclicked)
        self.mainLayout.addWidget(self.importButtonPB, line.postinc(), 1, 1, 1)

    def on_fromClipboardPBClicked(self):
        self.textEdit.setPlainText(pyperclip.paste())
        self.checkInputImport(autoset=True)

    def on_importPBclicked(self):
        isValid, errorMsg = self.checkInputImport(autoset=self.autoSetCB.isChecked())
        if isValid:
            if self.importer is not None:
                self.importer.toDatabase(self.collectionNameLE.text())
            self.close()
        else:
            _errorMsgBox = QtWidgets.QErrorMessage(self)
            _errorMsgBox.showMessage(errorMsg)

    def getSelectedImportFormat(self) -> str:
        selectedFormat = None
        for i in range(self.formatSelectLayout.count()):
            radioButton = self.formatSelectLayout.itemAt(i).widget()
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
        elif format == "EDHRec url":
            # TODO use url import button ?
            self.importer = EDHRec_importer(self)
            isValid, errorMsg = self.importer.loadInput(self.textEdit.toPlainText())
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
                    qt.findAttrInParents(self, "keyruneFontId"))))
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
        self.sideboardList = []
        self.commanderList = []
        self.companionList = []

    def toDatabase(self, deckName):
        if self.parent.collectionChooser.currentText() == "Deck":
            formatKey = constants.DEFAULT_DECK_FORMAT
            if hasattr(self.parent, "deckFormatCB"):
                formatKey = self.parent.deckFormatCB.currentData()
            connector.createDeck(
                deckName,
                self.deckList,
                sideboard=self.sideboardList,
                commander=self.commanderList,
                companion=self.companionList,
                format=formatKey,
            )
        elif self.parent.collectionChooser.currentText() == "Collection":
            connector.createCollection(
                deckName,
                self.deckList + self.sideboardList + self.commanderList + self.companionList,
            )
        else:
            raise NotImplementedError


class EDHRec_importer(importer):
    """
    Example link : https://edhrec.com/deckpreview/TV66-4LUHUNBJIO80_f4Rw
    Parses the Card Kingdom export URL embedded in the page to obtain the
    decklist (quantities and card names), then resolves each card via Scryfall.
    """
    def parseInput(self, url: str) -> list[tuple[int, str]]:
        """Return the (quantity, card name) entries parsed from the EDHRec page."""
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        # EDHRec embeds the decklist as a percent-encoded query parameter in the
        # Card Kingdom export link (e.g. .../builder?...&c=1%20Card%20Name%0A1%20...).
        export_url = None
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if 'cardkingdom' in href and 'c=1' in href:
                export_url = href
                break
        if export_url is None:
            raise ValueError("Could not find EDHRec Card Kingdom export link")

        parsed = urllib.parse.urlparse(export_url)
        query = urllib.parse.parse_qs(parsed.query)
        deck_param = query.get('c', [None])[0]
        if not deck_param:
            raise ValueError("Card Kingdom export link is missing the decklist parameter")

        # Lines are separated by percent-encoded newlines. Each line is "<qty> <name>".
        raw_lines = deck_param.replace('%0D%0A', '\n').replace('%0A', '\n').split('\n')
        entries = []
        for line in raw_lines:
            line = urllib.parse.unquote(line, encoding='utf-8', errors='replace').strip()
            if not line:
                continue
            match = re.fullmatch(r'(\d+)\s+(.*)', line)
            if match is None:
                logging.warning(f"Skipping malformed EDHRec deck line: {line!r}")
                continue
            qty = int(match.group(1))
            card_name = match.group(2)
            entries.append((qty, card_name))
        return entries

    def loadInput(self, url) -> bool:
        isValid = True
        errorMsg = ""

        try:
            entries = self.parseInput(url)
        except ValueError as e:
            return False, str(e)

        self.deckList = []
        for qty, card_name in entries:
            cards = scryfall.searchCards({"name": card_name}, exact=True)
            if len(cards) == 0:
                isValid = False
                errorMsg += f"\ncould not find {card_name=}"
            else:
                self.deckList.append([qty, cards[0]["id"]])
        return isValid, errorMsg


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
        self.sideboardList = []
        self.commanderList = []
        self.companionList = []
        section = "main"
        for line in lines:
            stripped = line.strip()
            header = stripped.lower()
            if header in ("deck", "main", "mainboard"):
                section = "main"
                continue
            if header in ("sideboard", "side board"):
                section = "sideboard"
                continue
            if header == "commander":
                section = "commander"
                continue
            if header == "companion":
                section = "companion"
                continue
            if not stripped or stripped.startswith("#"):
                continue
            matched = re.fullmatch(r"(\d+)\s(.*)", stripped)
            if matched is None:
                errorMsg += f"\nError on line {line=}"
                continue
            qty, cardName = matched.groups()
            qty = int(qty)
            # MTGA exports use the ligature Æ for cards such as "Aether Flash".
            # Scryfall's canonical name uses "Ae", so normalize before searching.
            cardName = cardName.replace("\u00c6", "Ae")
            cards = scryfall.searchCards({"name": cardName}, exact=True)
            if len(cards) == 0:
                isValid = False
                errorMsg += f"\ncould not find {cardName=}"
                continue
            if section == "commander":
                targetList = self.commanderList
            elif section == "companion":
                targetList = self.companionList
            elif section == "sideboard":
                targetList = self.sideboardList
            else:
                targetList = self.deckList
            card = cards[0]
            sets = scryfall.getCardReprints(card["id"])
            if len(sets) > 1 and not autoSet:
                _dialog = SetChooserDialog(parent=self.parent, cardName=cardName, sets=sets)
                i = _dialog.exec()
                set = sets[i]
                cardId = scryfall.getCardReprintId(card["id"], set)  # TODO handle lang ?
                targetList.append([qty, cardId])
            else:
                targetList.append([qty, card["id"]])
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
            isProbableHeader = (
                "name" in [_.lower() for _ in row] or
                "card" in [_.lower() for _ in row] or
                "card_name" in [_.lower() for _ in row]
            )
            # Skip header by looking at "name" in real columns names line
            if headerLine is None and not isProbableHeader:
                next
            elif headerLine is None and isProbableHeader:
                headerLine = i
                columns = row
            elif headerLine is not None:
                card = {}
                for i, v in enumerate(row):
                    if v != '' and i < len(columns):  # Pucatrade has wrongly formated csv, missing one header column
                        card.update({columns[i]: v})
                cards.append(card)

        # Check if Scryfall ID is in the available keys (Urza gatherer)
        # Urza Gatherer : "Scryfall ID"
        scryFallIdDictKey = None
        nameKey = None
        setKey = None
        availableKeys = [_.lower() for _ in cards[0].keys()]
        if "Scryfall ID".lower() in availableKeys:
            scryFallIdDictKey = list(cards[0].keys())[availableKeys.index("Scryfall ID".lower())]
        POSSIBLE_NAME_KEYS = ["Name", "Card", "Card_name"]
        for possibleNameKey in POSSIBLE_NAME_KEYS:
            if nameKey is None:
                if possibleNameKey.lower() in availableKeys:
                    nameKey = list(cards[0].keys())[availableKeys.index(possibleNameKey.lower())]
        POSSIBLE_SET_KEYS = ["Edition", "Set_code", "Set code", "Code", "Set"]
        for possibleSetKey in POSSIBLE_SET_KEYS:
            if setKey is None:
                if possibleSetKey.lower() in availableKeys:
                    setKey = list(cards[0].keys())[availableKeys.index(possibleSetKey.lower())]

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
            if scryFallIdDictKey is not None and scryFallIdDictKey in card.keys():
                if countDictKey is not None and countDictKey in card.keys():
                    self.deckList.append([card[countDictKey], card[scryFallIdDictKey]])
                else:  # if no quantity is given, assume one of each
                    self.deckList.append([1, card[scryFallIdDictKey]])
            elif nameKey is not None and setKey is not None:
                foundCards = []
                foundCard = None
                setCodeToMatch = None
                setName = card[setKey]
                if setName.lower() in [_["code"] for _ in scryfall.getSets()]:
                    setCodeToMatch = setName.lower()
                    foundCards = scryfall.searchCards({"name": card[nameKey], "set": setName}, exact=True)
                    if len(foundCards) == 0:
                        logging.error(f"could not load {card}, switching to accepting other sets")
                        foundCards = scryfall.searchCards({"name": card[nameKey]}, exact=True)
                else:
                    possibleSets = [_["code"] for _ in scryfall.getSets() if _["name"] == setName]
                    if len(possibleSets) == 0:
                        if not autoSet:
                            # TODO handle non auto sets
                            logging.warning(f"could not find {card=} in the given set")
                        foundCards = scryfall.searchCards({"name": card[nameKey]}, exact=True)
                    else:
                        setCodeToMatch = possibleSets[0].lower()
                        foundCards = scryfall.searchCards({"name": card[nameKey], "set": possibleSets[0]}, exact=True)
                if foundCards:
                    foundCard = next(
                        (found for found in foundCards if found["set"].lower() == setCodeToMatch),
                        foundCards[0],
                    )
                else:
                    logging.error(f"could not load {card}")
                if foundCard is not None:
                    if countDictKey is not None:
                        self.deckList.append([card[countDictKey], foundCard["id"]])
                    else:
                        self.deckList.append([1, foundCard["id"]])
            else:
                logging.error(f"Could not import {card}")

        return True, ""  # TODO grab errors


class MTGO_DEK_importer(importer):
    """
    .dek "xml" format
    """
    def loadInput(self, text: str) -> bool:
        self.deckList = []
        self.sideboardList = []
        self.commanderList = []
        self.companionList = []
        xmlRoot = lxml.etree.fromstring(text.encode(encoding="utf-8"))
        for card in xmlRoot.findall("Cards"):
            qty = int(card.attrib["Quantity"])
            mtgoId = card.attrib["CatID"]
            cardData = scryfall.getCardByMTGOId(int(mtgoId))
            if cardData is None:
                logging.error(f"Could not find card for MTGO id {mtgoId}")
                continue
            isSideboard = card.attrib.get("Sideboard", "false").lower() == "true"
            isCompanion = isSideboard and "companion" in (
                cardData.get("oracle_text", "") + " " + " ".join(cardData.get("keywords", []))
            ).lower()
            if isCompanion:
                targetList = self.companionList
            elif isSideboard:
                targetList = self.sideboardList
            else:
                targetList = self.deckList
            targetList.append(
                [qty, cardData["id"]]
            )
        return True, ""  # TODO grab errors
