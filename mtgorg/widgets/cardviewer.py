from PySide6 import QtWidgets, QtGui, QtCore, QtNetwork, QtSvgWidgets
import logging
import urllib
import os

from lib import scryfall, utils, qt
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

            if "sets" not in card:
                card["sets"] = scryfall.getCardReprints(card["id"])

            sets = []
            for setCode in card["sets"]:
                setName = scryfall.getSetDataByCode(setCode, "name")
                if setName is None:
                    logging.debug(f"Skipping unknown set code '{setCode}' in reprint list")
                    continue
                setId = scryfall.getSetDataByCode(setCode, "id")
                setYear = scryfall.getSetReleaseYear(setId) if setId else None
                sets.append((setName, setYear, setCode))
            sets.sort(key=lambda s: (s[1] is None, s[1]))

            self.dataReady.emit({
                "card": card,
                "cardFace": self._cardFace,
                "forceRefresh": self._forceRefresh,
                "setIconSvgData": setIconSvgData,
                "sets": sets,
            })
        except Exception as e:
            logging.warning(f"CardDisplayWorker error: {e}")
            self.failed.emit(str(e))


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


class SetChangeWorker(QtCore.QObject):
    ready = QtCore.Signal(list)
    failed = QtCore.Signal(str)

    def __init__(self, cardId: str, setCode: str, lang: str):
        super().__init__()
        self._cardId = cardId
        self._setCode = setCode
        self._lang = lang

    def run(self):
        try:
            ids = scryfall.getCardReprintId(self._cardId, self._setCode, lang=self._lang)
            self.ready.emit(ids)
        except Exception as e:
            self.failed.emit(str(e))


class CardViewer(QtWidgets.QWidget):
    # To Build
    def __init__(self, parent=None, **kwargs):
        super(CardViewer, self).__init__(parent=parent, **kwargs)
        self.setupUi()
        if constants.IMG_DOWNLOAD_METHOD == "qt":
            self.imgDownloader = ImageDownloader()
            self.imgDownloader.finished.connect(self.saveCardImg)

    def setupUi(self):
        self.mainLayout = QtWidgets.QGridLayout(self)

        line = utils.counter()

        self.randomCardPB = QtWidgets.QPushButton("View random card \u2680")
        self.randomCardPB.clicked.connect(self.on_randomCardPBClicked)
        self.mainLayout.addWidget(self.randomCardPB, line.val(), 0)
        self.addToCurrentPB = QtWidgets.QPushButton("Add to current >>")
        self.addToCurrentPB.clicked.connect(self.on_add)
        self.mainLayout.addWidget(self.addToCurrentPB, line.postinc(), 1)

        # Card Name + Mana
        self.nameLabel = QtWidgets.QLabel("")
        self.nameLabel.setStyleSheet("font-size: 16pt;")
        self.mainLayout.addWidget(self.nameLabel, line.val(), 0)
        self.manacostLabel = QtWidgets.QLabel()
        self.mainLayout.addWidget(self.manacostLabel, line.postinc(), 1)

        # Set icon + Name + Year
        self.setIconSvg = QtSvgWidgets.QSvgWidget()
        self.setIconSvg.setMaximumHeight(36)
        self.mainLayout.addWidget(self.setIconSvg, line.val(), 0)
        self.setSelect = QtWidgets.QComboBox()
        self.mainLayout.addWidget(self.setSelect, line.postinc(), 1)

        # Face Selector
        self.cardFaceChooser = QtWidgets.QPushButton("See other face \u21B7")
        self.cardFaceChooser.setVisible(False)
        self.cardFaceChooser.clicked.connect(self.on_cardflip)
        self.mainLayout.addWidget(self.cardFaceChooser, line.postinc(), 0)

        # Card Img
        self.cardImgGraphicsView = qt.ResizingGraphicsView()
        self.cardImgGraphicsView.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.mainLayout.addWidget(self.cardImgGraphicsView, line.postinc(), 0, 1, 2)
        self.reloadCardShortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+R'), self)
        self.reloadCardShortcut.activated.connect(self.on_reloadCardData)

        # Oracle text
        self.cardOracleTextLabel = QtWidgets.QTextEdit()
        self.cardOracleTextLabel.setReadOnly(True)
        self.cardOracleTextLabel.setMaximumHeight(160)
        self.mainLayout.addWidget(self.cardOracleTextLabel, line.postinc(), 0, 1, 2)

        # Card Link
        self.scryfallUriLabel = QtWidgets.QLabel("uri")
        self.scryfallUriLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.scryfallUriLabel.setOpenExternalLinks(True)
        # self.scryfallUriLabel.linkActivated.connect(self.on_scryfallLinkClicked)
        self.mainLayout.addWidget(self.scryfallUriLabel, line.val(), 0)

        # Card price
        self.avgPriceLabel = QtWidgets.QLabel("price")
        self.mainLayout.addWidget(self.avgPriceLabel, line.postinc(), 1)

    def on_reloadCardData(self):
        self.display(self.card["id"], forceRefresh=True)

    def on_add(self):
        # TODO check when already present to raise qty instead of adding other line
        qt.findAttrInParents(self, "decklist").cardsList.addCard(self.card)

    def on_scryfallLinkClicked(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.uri))

    def on_randomCardPBClicked(self):
        self._random_thread = QtCore.QThread()
        self._random_worker = RandomCardFetchWorker()
        self._random_worker.moveToThread(self._random_thread)
        self._random_thread.started.connect(self._random_worker.run)
        self._random_worker.ready.connect(self.display)
        self._random_worker.failed.connect(self._on_display_failed)
        self._random_worker.ready.connect(self._random_thread.quit)
        self._random_worker.failed.connect(self._random_thread.quit)
        self._random_worker.ready.connect(self._random_worker.deleteLater)
        self._random_worker.failed.connect(self._random_worker.deleteLater)
        self._random_thread.finished.connect(self._random_thread.deleteLater)
        self._random_thread.start()

    def saveCardImg(self, image, cardId):
        logging.info(f"saved image for {cardId=}")
        saveCardImg(image, cardId)
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
        self.cardImgGraphicsView.fitInView(bounds, QtCore.Qt.KeepAspectRatio)

    def setManaFont(self):
        if self.manacostLabel.font().family() != "Proxyglyph":
            font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                qt.findAttrInParents(self, "proxyglyphFontId")))
            font.setPointSize(24)
            self.manacostLabel.setFont(font)

    def colorSetIcon(self, data: QtCore.QByteArray, rarity: str = "C"):
        if rarity in constants.RARITIES.keys():
            try:
                color = constants.RARITIES[rarity]["color"]
            except TypeError:
                logging.warning()
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
        # Cancel any in-progress fetch
        if hasattr(self, '_display_thread') and self._display_thread.isRunning():
            self._display_thread.quit()
            self._display_thread.wait()
        self.nameLabel.setText("Loading...")
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

    def _on_display_data_ready(self, data: dict):
        card = data["card"]
        cardFace = data["cardFace"]
        sets = data["sets"]
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

        if "card_faces" in self.card.keys():
            manaCost = self.card["card_faces"][0]["mana_cost"]
        else:
            manaCost = self.card["mana_cost"]

        self.manacostLabel.setText(utils.setManaText(manaCost))
        self.setManaFont()

        setIconSvgData = self.colorSetIcon(setIconSvgData, self.card["rarity"])
        if setIconSvgData is not None:
            self.setIconSvg.load(QtCore.QByteArray(setIconSvgData))
            self.setIconSvg.renderer().setAspectRatioMode(QtCore.Qt.KeepAspectRatio)

        try:
            self.setSelect.currentIndexChanged.disconnect()
        except (RuntimeError, RuntimeWarning):
            ...
        self.setSelect.clear()

        selectedText = ""
        for setName, setYear, setCode in sets:
            setText = f"{setName} ({setCode.upper()}) - {setYear}"
            self.setSelect.addItem(setText, setCode)
            if self.card["set"] == setCode:
                selectedText = setText
        self.setSelect.setCurrentText(selectedText)
        self.setSelect.currentIndexChanged.connect(self.on_setChange)

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

        if constants.USE_BULK_FILES and not isCardImageCached(cardId):
            pass
        elif isCardImageCached(cardId) and not _hasManyFaces or constants.IMG_DOWNLOAD_METHOD == "direct":
            # TODO handle cache for multi face cards
            cardImgPath = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
            image = QtGui.QImage()
            image.load(cardImgPath.as_posix())
            self.displayPixmapCard(image)
        elif constants.IMG_DOWNLOAD_METHOD == "qt":
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

        self.avgPriceLabel.setText(
            str(utils.getFromDict(self.card, ["prices", constants.CURRENCY[0]])) + " " + constants.CURRENCY[1]
        )

    def _on_display_failed(self, error: str):
        logging.warning(f"Failed to display card: {error}")
        self.nameLabel.setText(f"Failed to load card")

    def downloadCardImg(self, imageUri, cardId):
        url = QtCore.QUrl.fromUserInput(imageUri)
        self.imgDownloader.start_download(url, cardId)

    def on_cardflip(self):
        self.display(self.card["id"], cardFace=(self.cardFace+1) % 2)

    def on_setChange(self):
        selectedSet = self.setSelect.itemData(self.setSelect.currentIndex())
        self._setchange_thread = QtCore.QThread()
        self._setchange_worker = SetChangeWorker(self.card["id"], selectedSet, self.card["lang"])
        self._setchange_worker.moveToThread(self._setchange_thread)
        self._setchange_thread.started.connect(self._setchange_worker.run)
        self._setchange_worker.ready.connect(self._on_set_change_ids_ready)
        self._setchange_worker.failed.connect(self._on_display_failed)
        self._setchange_worker.ready.connect(self._setchange_thread.quit)
        self._setchange_worker.failed.connect(self._setchange_thread.quit)
        self._setchange_worker.ready.connect(self._setchange_worker.deleteLater)
        self._setchange_worker.failed.connect(self._setchange_worker.deleteLater)
        self._setchange_thread.finished.connect(self._setchange_thread.deleteLater)
        self._setchange_thread.start()

    def _on_set_change_ids_ready(self, ids: list):
        if len(ids) == 0:
            logging.warning("No cards found for selected set")
            return
        # TODO Show card selector widget when len(ids) > 1
        self.display(ids[0])


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
        if reply.error() != QtNetwork.QNetworkReply.NoError:
            print("error: ", reply.errorString())
            return
        image = QtGui.QImage()
        image.loadFromData(reply.readAll())
        self.finished.emit(image, self.cardId)


def isCardImageCached(cardId) -> bool:
    cardImgPath = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
    return cardImgPath.is_file() and os.access(cardImgPath, os.R_OK)


def getCardImageFromUrl(url, cardId) -> str:
    cardImgPath = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
    if not (cardImgPath.is_file() and os.access(cardImgPath, os.R_OK)):
        urllib.request.urlretrieve(url, cardImgPath)
    return cardImgPath


def saveCardImg(image: QtGui.QImage, cardId: str):
    path = constants.DEFAULT_CARDIMAGES_LOCATION / cardId
    writer = QtGui.QImageWriter(path.as_posix(), format=QtCore.QByteArray("jpg"))
    writer.write(image)
