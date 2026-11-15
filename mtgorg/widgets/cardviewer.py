from PySide6 import QtWidgets, QtGui, QtCore, QtNetwork, QtSvgWidgets
import logging
import traceback
import urllib
import urllib.request
import os

from lib import deckrules, scryfall, utils, qt
import connector
import constants


class CardDisplayWorker(QtCore.QObject):
    """Fetches all card display data in a background thread."""
    dataReady = QtCore.Signal(dict)
    failed = QtCore.Signal(str)

    def __init__(self, cardId: str, cardFace: int = 0, forceRefresh: bool = False):
        super().__init__()
        self._cardId = cardId
        self._cardFace = cardFace
        self._forceRefresh = forceRefresh

    def run(self):
        try:
            card = scryfall.getCardById(self._cardId, force=self._forceRefresh)
            if card is None:
                self.failed.emit(f"Card {self._cardId} not found")
                return

            setIconSvgData = qt.fileData(scryfall.getSetSvg(card["set_id"]))

            printings = scryfall.getCardPrintings(card["id"])

            self.dataReady.emit({
                "card": card,
                "cardFace": self._cardFace,
                "forceRefresh": self._forceRefresh,
                "setIconSvgData": setIconSvgData,
                "printings": printings,
            })
        except Exception:
            logging.exception(f"CardDisplayWorker error while loading {self._cardId=}")
            self.failed.emit(traceback.format_exc())


class RandomCardFetchWorker(QtCore.QObject):
    ready = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def run(self):
        try:
            card = scryfall.getRandomCard()
            if card:
                self.ready.emit(card["id"])
        except Exception as e:
            self.failed.emit(str(e))


class CardViewer(QtWidgets.QWidget):
    # To Build
    replaceInDeckRequested: QtCore.Signal = QtCore.Signal(str, str)  # (old_card_id, new_card_id)

    def __init__(self, parent=None, **kwargs):
        super(CardViewer, self).__init__(parent=parent, **kwargs)
        self._deck_card_id: str | None = None
        self._display_thread: QtCore.QThread | None = None
        self._display_worker: CardDisplayWorker | None = None
        self._graveyard_threads: list[QtCore.QThread] = []
        self.setupUi()
        if constants.IMG_DOWNLOAD_METHOD == "qt":
            self.imgDownloader = ImageDownloader()
            self.imgDownloader.finished.connect(self.saveCardImg)

    def setupUi(self):
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setColumnStretch(0, 1)
        self.mainLayout.setColumnStretch(1, 0)

        line = utils.counter()

        self.randomCardPB = QtWidgets.QPushButton("View random card \u2680")
        self.randomCardPB.clicked.connect(self.on_randomCardPBClicked)
        self.mainLayout.addWidget(self.randomCardPB, line.val(), 0)
        self.addToCurrentPB = QtWidgets.QPushButton("Add to current >>")
        self.addToCurrentPB.setToolTip("Left-click adds to Main; right-click to choose a section")
        self.addToCurrentPB.clicked.connect(self.on_add)
        self.addToCurrentPB.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.addToCurrentPB.customContextMenuRequested.connect(self.on_addContextMenu)
        self.mainLayout.addWidget(self.addToCurrentPB, line.postinc(), 1)

        # Card Name + Mana
        self.nameLabel = QtWidgets.QLabel("")
        self.nameLabel.setStyleSheet("font-size: 16pt;")
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.mainLayout.addWidget(self.nameLabel, line.val(), 0)
        self.manacostLabel = QtWidgets.QLabel()
        self.manacostLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.mainLayout.addWidget(self.manacostLabel, line.postinc(), 1)

        # Set icon + Name + Year
        self.setIconSvg = QtSvgWidgets.QSvgWidget()
        self.setIconSvg.setMaximumHeight(36)
        self.printingSelect = QtWidgets.QComboBox()
        self.printingSelect.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.printingSelect.setMinimumContentsLength(24)
        self.printingSelect.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.printingSelect.currentIndexChanged.connect(self.on_printingChange)
        self.setInfoWidget = QtWidgets.QWidget()
        self.setInfoLayout = QtWidgets.QHBoxLayout(self.setInfoWidget)
        self.setInfoLayout.setContentsMargins(0, 0, 0, 0)
        self.setInfoLayout.addWidget(self.setIconSvg)
        self.setInfoLayout.addWidget(self.printingSelect, 1)
        self.mainLayout.addWidget(self.setInfoWidget, line.postinc(), 0, 1, 2)

        # Face Selector
        self.cardFaceChooser = QtWidgets.QPushButton("See other face \u21B7")
        self.cardFaceChooser.setVisible(False)
        self.cardFaceChooser.clicked.connect(self.on_cardflip)
        self.mainLayout.addWidget(self.cardFaceChooser, line.val(), 0)
        self.applyToDeckPB = QtWidgets.QPushButton("Apply set to deck \u2713")
        self.applyToDeckPB.setVisible(False)
        self.applyToDeckPB.clicked.connect(self.on_applyToDeck)
        self.mainLayout.addWidget(self.applyToDeckPB, line.postinc(), 1)

        # Card Img
        self.cardImgGraphicsView = qt.ResizingGraphicsView()
        self.cardImgGraphicsView.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing
            | QtGui.QPainter.RenderHint.SmoothPixmapTransform
        )
        self.mainLayout.addWidget(self.cardImgGraphicsView, line.postinc(), 0, 1, 2)
        self.reloadCardShortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+R'), self)
        self.reloadCardShortcut.activated.connect(self.on_reloadCardData)

        # English name (shown for non-English cards)
        self.englishNameLabel = QtWidgets.QLabel()
        self.englishNameLabel.setStyleSheet("font-style: italic; color: gray;")
        self.englishNameLabel.setVisible(False)
        self.mainLayout.addWidget(self.englishNameLabel, line.postinc(), 0, 1, 2)

        # Oracle text
        self.cardOracleTextLabel = QtWidgets.QTextEdit()
        self.cardOracleTextLabel.setReadOnly(True)
        self.cardOracleTextLabel.setMaximumHeight(160)
        self.mainLayout.addWidget(self.cardOracleTextLabel, line.postinc(), 0, 1, 2)

        # Card Link
        self.scryfallUriLabel = QtWidgets.QLabel("uri")
        self.scryfallUriLabel.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
        self.scryfallUriLabel.setOpenExternalLinks(True)
        # self.scryfallUriLabel.linkActivated.connect(self.on_scryfallLinkClicked)
        self.mainLayout.addWidget(self.scryfallUriLabel, line.val(), 0)

        # Card price
        self.avgPriceLabel = QtWidgets.QLabel("price")
        self.mainLayout.addWidget(self.avgPriceLabel, line.postinc(), 1)

    def on_reloadCardData(self):
        self.display(self.card["id"], forceRefresh=True)

    def display_from_deck(self, cardId: str):
        """Display a card that originates from the current deck/collection."""
        self._deck_card_id = cardId
        self.display(cardId)

    def display_from_db(self, cardId: str):
        """Display a card from the DB browser (no deck context)."""
        self._deck_card_id = None
        self.applyToDeckPB.setVisible(False)
        self.display(cardId)

    def on_add(self):
        self.addToSection("main")

    def addToSection(self, section: str):
        if not hasattr(self, "card"):
            return
        logging.info(f"Adding {self.card.get('name')} to {section}")
        qt.findAttrInParents(self, "decklist").cardsList.addCard(self.card, section=section)

    def on_addContextMenu(self, pos):
        if not hasattr(self, "card"):
            return
        stackType, stackName = qt.findAttrInParents(self, "deckSelector").getSelected()
        if stackType != "deck":
            return
        deck = connector.getDeck(stackName)
        if deck is None:
            return
        allowed = deckrules.allowedSections(deck.get("format", constants.DEFAULT_DECK_FORMAT))
        labels = {"commander": "Commander", "main": "Main", "sideboard": "Sideboard"}
        menu = QtWidgets.QMenu(self.addToCurrentPB)
        for section in ("commander", "main", "sideboard"):
            if section in allowed:
                action = menu.addAction(f"Add to {labels[section]}")
                action.setData(section)
        chosen = menu.exec(self.addToCurrentPB.mapToGlobal(pos))
        if chosen is not None:
            self.addToSection(chosen.data())

    def on_scryfallLinkClicked(self):
        if hasattr(self, 'card'):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.card.get('scryfall_uri', '')))

    def on_randomCardPBClicked(self):
        self._random_thread = QtCore.QThread()
        self._random_worker = RandomCardFetchWorker()
        self._random_worker.moveToThread(self._random_thread)
        self._random_thread.started.connect(self._random_worker.run)
        self._random_worker.ready.connect(self.display_from_db)
        self._random_worker.failed.connect(self._on_display_failed)
        self._random_worker.ready.connect(self._random_thread.quit)
        self._random_worker.failed.connect(self._random_thread.quit)
        self._random_worker.ready.connect(self._random_worker.deleteLater)
        self._random_worker.failed.connect(self._random_worker.deleteLater)
        self._random_thread.finished.connect(self._random_thread.deleteLater)
        self._random_thread.start()

    def saveCardImg(self, image, cardId):
        saveCardImg(image, cardId)
        logging.info(f"saved image for {cardId=}")
        self.displayPixmapCard(image)

    def displayPixmapCard(self, image):
        # display
        self.cardImgPixMap = QtGui.QPixmap.fromImage(image)
        self.scene = QtWidgets.QGraphicsScene()
        self.cardImgGraphicsView.setScene(self.scene)
        if any(isinstance(_, QtWidgets.QGraphicsPixmapItem) for _ in self.cardImgGraphicsView.scene().items()):
            self.cardImgGraphicsView.scene().clear()
        self.cardImgGraphicsView.scene().addPixmap(self.cardImgPixMap)
        bounds = self.cardImgGraphicsView.scene().itemsBoundingRect()
        self.cardImgGraphicsView.fitInView(bounds, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def setManaFont(self):
        if self.manacostLabel.font().family() != "Proxyglyph":
            font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                qt.findAttrInParents(self, "proxyglyphFontId")))
            font.setPointSize(24)
            self.manacostLabel.setFont(font)

    def colorSetIcon(self, data: str | None, rarity: str = "C") -> str | None:
        color: str
        if rarity in constants.RARITIES.keys():
            try:
                color = constants.RARITIES[rarity]["color"]
            except TypeError:
                logging.warning(f"could not find color for {rarity=}")
                color = "#00F"
        else:
            logging.warning(f"could not find color for {rarity=}")
            color = "#00F"
        if data is not None:
            if "#000" not in data:  # adding the path filling if not present
                splitText = "/></svg>"
                fillText = " fill=\"#000\" fill-rule=\"nonzero\""
                data = data.split(splitText)[0] + fillText + splitText
            data = data.replace("#000", color)
        return data

    def display(self, cardId: str, cardFace: int = 0, forceRefresh: bool = False):
        self.nameLabel.setText("Loading...")

        # Keep the previous thread alive until it finishes so Qt doesn't destroy it early.
        if self._display_thread is not None and self._display_thread.isRunning():
            self._bury_thread(self._display_thread)
            self._cleanup_graveyard()

        self._display_thread = QtCore.QThread()
        self._display_worker = CardDisplayWorker(cardId, cardFace, forceRefresh)
        self._display_worker.moveToThread(self._display_thread)
        self._display_thread.started.connect(self._display_worker.run)
        self._display_worker.dataReady.connect(self._on_display_data_ready)
        self._display_worker.failed.connect(self._on_display_failed)
        self._display_worker.dataReady.connect(self._display_thread.quit)
        self._display_worker.failed.connect(self._display_thread.quit)
        self._display_worker.dataReady.connect(self._display_worker.deleteLater)
        self._display_worker.failed.connect(self._display_worker.deleteLater)
        self._display_thread.start()

    def _bury_thread(self, thread: QtCore.QThread):
        """Keep a finished thread alive briefly so Qt doesn't destroy it while running."""
        if thread in self._graveyard_threads:
            return
        self._graveyard_threads.append(thread)

    def _cleanup_graveyard(self):
        aliveThreads = []
        for thread in self._graveyard_threads:
            try:
                if thread is not None and thread.isRunning():
                    aliveThreads.append(thread)
            except RuntimeError:
                pass
        self._graveyard_threads = aliveThreads

    def _on_display_data_ready(self, data: dict):
        card = data["card"]
        cardFace = data["cardFace"]
        printings = data["printings"]
        setIconSvgData = data["setIconSvgData"]

        self.card = card
        cardId = card["id"]

        if "printed_name" in self.card.keys():
            self.nameLabel.setText(self.card["printed_name"])
        else:
            self.nameLabel.setText(self.card["name"])

        if self.card["lang"] == "ph":
            phyrexianFont = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                qt.findAttrInParents(self, "phyrexianFontId")
            ))
            self.nameLabel.setFont(phyrexianFont)
        else:
            self.nameLabel.setFont(QtGui.QFont())
            self.nameLabel.setStyleSheet("font-size: 16pt;")

        if self.card["lang"] != "en" and "printed_name" in self.card:
            self.englishNameLabel.setText(self.card["name"])
            self.englishNameLabel.setVisible(True)
        else:
            self.englishNameLabel.setVisible(False)

        if "card_faces" in self.card.keys():
            manaCost = self.card["card_faces"][0]["mana_cost"]
        else:
            manaCost = self.card["mana_cost"]

        self.manacostLabel.setText(utils.setManaText(manaCost))
        self.setManaFont()

        setIconSvgData = self.colorSetIcon(setIconSvgData, self.card["rarity"])
        if setIconSvgData is not None:
            self.setIconSvg.load(QtCore.QByteArray(setIconSvgData.encode("utf-8")))
            self.setIconSvg.renderer().setAspectRatioMode(QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        self.printingSelect.blockSignals(True)
        self.printingSelect.clear()
        selectedIndex = 0
        for index, printing in enumerate(printings):
            self.printingSelect.addItem(getPrintingLabel(printing), printing["id"])
            if printing["id"] == cardId:
                selectedIndex = index
        self.printingSelect.setCurrentIndex(selectedIndex)
        self.printingSelect.blockSignals(False)

        self.cardFaceChooser.setVisible(False)
        self.cardFace = cardFace
        _hasManyFaces = False
        if utils.getFromDict(self.card, ["image_uris"], None) is not None:
            imageUri = utils.getFromDict(self.card, ["image_uris", constants.IMG_SIZE])
        else:
            if len(self.card["card_faces"]) > 1:
                _hasManyFaces = True
                self.cardFaceChooser.setVisible(True)
            imageUri = utils.getFromDict(
                self.card, ["card_faces", cardFace, "image_uris", constants.IMG_SIZE])

        imageAction = getCardImageAction(cardId, imageUri, _hasManyFaces)
        if imageAction == "load":
            # TODO handle cache for multi face cards
            cardImgPath = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
            image = QtGui.QImage()
            image.load(cardImgPath.as_posix())
            self.displayPixmapCard(image)
        elif imageAction == "download":
            if self.cardImgGraphicsView.scene() is not None:
                if any(isinstance(_, QtWidgets.QGraphicsPixmapItem) for _ in self.cardImgGraphicsView.scene().items()):
                    self.cardImgGraphicsView.scene().clear()
            self.downloadCardImg(imageUri, cardId)

        # Oracle text
        text = self.card["type_line"] + "\n"
        if "power" in self.card.keys():
            text += self.card["power"] + "/" + self.card["toughness"] + "\n"
        if "oracle_text" in self.card.keys():
            text += self.card["oracle_text"] + "\n"
        else:
            text += self.card["card_faces"][cardFace]["oracle_text"] + "\n"
        self.cardOracleTextLabel.setText(text)

        try:
            self.scryfallUriLabel.setText(f"<a href=\"{self.card['related_uris']['gatherer']}\">Gatherer Link</a>")
        except KeyError:
            self.scryfallUriLabel.setText(f"<a href=\"{self.card['scryfall_uri']}\">Scryfall Link</a>")

        _price = utils.getFromDict(self.card, ["prices", constants.CURRENCY[0]])
        _foil_key = constants.CURRENCY[0] + "_foil"
        _foil_price = utils.getFromDict(self.card, ["prices", _foil_key])
        if _price is not None:
            _price_text = f"{_price} {constants.CURRENCY[1]}"
        elif _foil_price is not None:
            _price_text = f"{_foil_price} {constants.CURRENCY[1]} (foil)"
        else:
            _price_text = "N/A"
        self.avgPriceLabel.setText(_price_text)

        # Show "Apply to deck" button only when the displayed card differs from the deck's card
        if self._deck_card_id is not None and self.card["id"] != self._deck_card_id:
            self.applyToDeckPB.setVisible(True)
        else:
            self.applyToDeckPB.setVisible(False)

    def _on_display_failed(self, error: str):
        logging.error("Failed to display card:\n%s", error)
        self.nameLabel.setText("Failed to load card")

    def on_applyToDeck(self):
        if self._deck_card_id is not None and self.card["id"] != self._deck_card_id:
            old_id = self._deck_card_id
            self._deck_card_id = self.card["id"]
            self.applyToDeckPB.setVisible(False)
            self.replaceInDeckRequested.emit(old_id, self.card["id"])

    def downloadCardImg(self, imageUri, cardId):
        url = QtCore.QUrl.fromUserInput(imageUri)
        self.imgDownloader.start_download(url, cardId)

    def on_cardflip(self):
        self.display(self.card["id"], cardFace=(self.cardFace+1) % 2)

    def on_printingChange(self):
        if not hasattr(self, "card"):
            return
        selectedCardId = self.printingSelect.itemData(self.printingSelect.currentIndex())
        if selectedCardId is None or selectedCardId == self.card["id"]:
            return
        self.display(selectedCardId)


class ImageDownloader(QtCore.QObject):
    finished = QtCore.Signal(QtGui.QImage, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.finished.connect(self.handle_finished)

    def start_download(self, url, cardId):
        self.cardId = cardId
        self.manager.get(QtNetwork.QNetworkRequest(url))

    def handle_finished(self, reply):
        if reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            print("error: ", reply.errorString())
            return
        image = QtGui.QImage()
        image.loadFromData(reply.readAll())
        self.finished.emit(image, self.cardId)


def getPrintingLabel(card: dict) -> str:
    frameEffects = set(card.get("frame_effects") or [])
    labels = []
    for effect, label in (
        ("showcase", "showcase"),
        ("extendedart", "extended art"),
        ("borderless", "borderless"),
        ("inverted", "inverted"),
        ("etched", "etched"),
        ("fracturefoil", "fracture foil"),
    ):
        if effect in frameEffects:
            labels.append(label)
    promoTypes = card.get("promo_types") or []
    if promoTypes:
        labels.append("promo: " + ", ".join(promoTypes))
    finishes = card.get("finishes") or []
    if finishes == ["foil"]:
        labels.append("foil only")
    if card.get("lang") not in (None, "en"):
        labels.append(str(card.get("lang")).upper())
    if not labels:
        labels.append("regular")

    setName = card.get("set_name", card.get("set", "").upper())
    setCode = card.get("set", "").upper()
    collectorNumber = card.get("collector_number", "")
    return f"{setName} ({setCode}) #{collectorNumber} - {', '.join(labels)}"


def isCardImageCached(cardId) -> bool:
    cardImgPath = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
    return cardImgPath.is_file() and os.access(cardImgPath, os.R_OK)


def getCardImageAction(cardId, imageUri, hasManyFaces: bool = False) -> str:
    """Return 'load', 'download', or 'none' for the card image display path."""
    if isCardImageCached(cardId) and not hasManyFaces:
        return "load"
    if imageUri is not None and constants.IMG_DOWNLOAD_METHOD == "qt":
        return "download"
    return "none"


def getCardImageFromUrl(url, cardId) -> str:
    cardImgPath = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
    if not (cardImgPath.is_file() and os.access(cardImgPath, os.R_OK)):
        urllib.request.urlretrieve(url, cardImgPath)
    return cardImgPath


def saveCardImg(image: QtGui.QImage, cardId: str):
    path = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
    writer = QtGui.QImageWriter(path.as_posix(), b"jpg")
    writer.write(image)
