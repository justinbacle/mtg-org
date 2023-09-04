from PySide6 import QtWidgets, QtGui, QtCore, QtNetwork, QtSvgWidgets
import logging
import urllib

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from lib import scryfall, utils, qt  # noqa E402

import constants  # noqa E402


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
        scryfall.getCardById(self.card["id"], force=True)
        if utils.getFromDict(self.card, ["image_uris"], None) is not None:
            # TODO fix whan dual faced card download fixed
            imageUri = utils.getFromDict(self.card, ["image_uris", constants.IMG_SIZE])
            self.downloadCardImg(imageUri, self.card["id"])

    def on_add(self):
        # TODO check when already present to raise qty instead of adding other line
        qt.findAttrInParents(self, "decklist").cardsList.addCard(self.card)

    def on_scryfallLinkClicked(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.uri))

    def on_randomCardPBClicked(self):
        self.display(scryfall.getRandomCard()["id"])

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
            color = constants.RARITIES[rarity]["color"]
        else:
            logging.warning(f"could not find color for {rarity=}")
            color = "#00F"
        if "#000" not in data:  # adding the path filling if not present
            splitText = "/></svg>"
            fillText = " fill=\"#000\" fill-rule=\"nonzero\""
            data = data.split(splitText)[0] + fillText + splitText
        data = data.replace("#000", color)
        return data

    def display(self, cardId: str, cardFace: int = 0):
        self.card = scryfall.getCardById(cardId)
        if "printed_name" in self.card.keys():
            self.nameLabel.setText(self.card["printed_name"])
        else:
            self.nameLabel.setText(self.card["name"])

        if "card_faces" in self.card.keys():
            manaCost = self.card["card_faces"][0]["mana_cost"]
        else:
            manaCost = self.card["mana_cost"]

        self.manacostLabel.setText(utils.setManaText(manaCost))
        self.setManaFont()

        setIconSvgData = qt.fileData(scryfall.getSetSvg(self.card["set_id"]))
        setIconSvgData = self.colorSetIcon(setIconSvgData, self.card["rarity"])
        self.setIconSvg.load(QtCore.QByteArray(setIconSvgData))
        self.setIconSvg.renderer().setAspectRatioMode(QtCore.Qt.KeepAspectRatio)

        try:
            self.setSelect.currentIndexChanged.disconnect()
        except RuntimeError:
            ...
        self.setSelect.clear()

        # reprints handling
        if "sets" not in self.card.keys():
            self.card.update({"sets": scryfall.getCardReprints(self.card["id"])})

        sets = []
        for setCode in self.card["sets"]:
            setName = scryfall.getSetDataByCode(setCode, 'name')
            setYear = scryfall.getSetReleaseYear(scryfall.getSetDataByCode(setCode, 'id'))
            sets.append((setName, setYear, setCode))
        # sort reprints by year
        sets.sort(key=lambda _: _[1])
        for _set in sets:
            setName, setYear, setCode = _set
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
            if len(self.card['card_faces']) > 1:
                _hasManyFaces = True
                self.cardFaceChooser.setVisible(True)
            imageUri = utils.getFromDict(
                self.card, ["card_faces", cardFace, "image_uris", constants.IMG_SIZE])

        if isCardImageCached(cardId) and not _hasManyFaces or constants.IMG_DOWNLOAD_METHOD == "direct":
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

        # gatherer/scryfall uri
        try:
            self.scryfallUriLabel.setText(f"<a href=\"{self.card['related_uris']['gatherer']}\">Gatherer Link</a>")
        except KeyError:
            self.scryfallUriLabel.setText(f"<a href=\"{self.card['scryfall_uri']}\">Scryfall Link</a>")

        # price
        self.avgPriceLabel.setText(
            str(utils.getFromDict(self.card, ["prices", constants.CURRENCY[0]])) + " " + constants.CURRENCY[1]
        )

    def downloadCardImg(self, imageUri, cardId):
        url = QtCore.QUrl.fromUserInput(imageUri)
        self.imgDownloader.start_download(url, cardId)

    def on_cardflip(self):
        self.display(self.card["id"], cardFace=(self.cardFace+1) % 2)

    def on_setChange(self):
        selectedSet = self.setSelect.itemData(self.setSelect.currentIndex())
        self.display(scryfall.getCardReprintId(self.card["id"], selectedSet, lang=self.card["lang"]))


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
