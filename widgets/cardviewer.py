from PySide6 import QtWidgets, QtGui, QtCore, QtNetwork, QtSvgWidgets

import urllib
from pathlib import Path

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from lib import scryfall, utils, qt  # noqa E402

import constants  # noqa E402
import config  # noqa E402


class CardViewer(QtWidgets.QWidget):
    # To Build
    def __init__(self, parent=None, **kwargs):
        super(CardViewer, self).__init__(parent=parent, **kwargs)
        self.setupUi()
        if config.IMG_DOWNLOAD_METHOD == "qt":
            self.imgDownloader = ImageDownloader()
            self.imgDownloader.finished.connect(self.displayPixmapCard)

    def setupUi(self):
        self.mainLayout = QtWidgets.QGridLayout(self)

        line = 0

        self.addToCurrentPB = QtWidgets.QPushButton("Add to current >>")
        self.addToCurrentPB.clicked.connect(self.on_add)
        self.mainLayout.addWidget(self.addToCurrentPB, (line := line+1) - 1, 1)

        # Card Name + Mana
        self.nameLabel = QtWidgets.QLabel("Name")
        self.mainLayout.addWidget(self.nameLabel, line, 0)
        self.manacostLabel = QtWidgets.QLabel("{M}{A}{N}{A}{0}")
        self.mainLayout.addWidget(self.manacostLabel, (line := line+1) - 1, 1)

        # Set icon + Name + Year
        self.setIconSvg = QtSvgWidgets.QSvgWidget()
        self.setIconSvg.setMaximumHeight(36)
        self.mainLayout.addWidget(self.setIconSvg, line, 0)
        self.setSelect = QtWidgets.QComboBox()
        self.mainLayout.addWidget(self.setSelect, (line := line+1) - 1, 1)

        # Card Img
        self.cardImgGraphicsView = QtWidgets.QGraphicsView()
        self.cardImgGraphicsView.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.mainLayout.addWidget(self.cardImgGraphicsView, (line := line+1) - 1, 0, 1, 2)

        # Card Link
        self.scryfallUriLabel = QtWidgets.QLabel("uri")
        self.scryfallUriLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.scryfallUriLabel.linkActivated.connect(self.on_scryfallLinkClicked)
        self.mainLayout.addWidget(self.scryfallUriLabel, line, 0)

        # Card price
        self.avgPriceLabel = QtWidgets.QLabel("price")
        self.mainLayout.addWidget(self.avgPriceLabel, (line := line+1) - 1, 1)

    def on_add(self):
        self.parent().parent().parent().decklist.cardsList.addCard(self.card)

    def on_scryfallLinkClicked(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.card['related_uris']['gatherer']))

    def displayPixmapCard(self, image):
        self.cardImgPixMap = QtGui.QPixmap.fromImage(image)
        if self.cardImgGraphicsView.scene() is None:
            self.cardImgGraphicsView.setScene(QtWidgets.QGraphicsScene())
        if any(isinstance(_, QtWidgets.QGraphicsPixmapItem) for _ in self.cardImgGraphicsView.scene().items()):
            self.cardImgGraphicsView.scene().clear()
        self.cardImgGraphicsView.scene().addPixmap(self.cardImgPixMap)
        bounds = self.cardImgGraphicsView.scene().itemsBoundingRect()
        self.cardImgGraphicsView.fitInView(bounds, QtCore.Qt.KeepAspectRatio)

    def setManaFont(self):
        if self.manacostLabel.font().family() != "Mana":
            self.manacostLabel.setFont(
                QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(
                    self.parent().parent().parent().manaFontId)))

    def colorSetIcon(self, data: QtCore.QByteArray, rarity: str = "C"):
        if rarity in constants.RARITIES.keys():
            color = constants.RARITIES[rarity]["color"]
        else:
            color = "#00F"
        if "#000" not in data:  # adding the path filling if not present
            splitText = "/></svg>"
            fillText = " fill=\"#000\" fill-rule=\"nonzero\""
            data = data.split(splitText)[0] + fillText + splitText
        data = data.replace("#000", color)
        return data

    def display(self, cardId: str):
        self.card = scryfall.getCardById(cardId)
        self.nameLabel.setText(self.card["name"])
        self.manacostLabel.setText(utils.setManaText(utils.getFromDict(self.card, ["mana_cost"], "")))
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
        for set in self.card["sets"]:
            setName = scryfall.getSetDataByCode(set, 'name')
            setYear = scryfall.getSetReleaseYear(scryfall.getSetDataByCode(set, 'id'))
            setText = f"{setName} ({set.upper()}) - {setYear}"
            self.setSelect.addItem(setText, set)
            if self.card["set"] == set:
                selectedText = setText
        self.setSelect.setCurrentText(selectedText)
        self.setSelect.currentIndexChanged.connect(self.on_setChange)

        if utils.getFromDict(self.card, ["image_uris"], None) is not None:
            imageUri = utils.getFromDict(self.card, ["image_uris", config.IMG_SIZE])
        else:
            # TODO handle two_sided cards -> len(self.card['card_faces']) > 1
            imageUri = utils.getFromDict(
                self.card, ["card_faces", 0, "image_uris", config.IMG_SIZE])

        if config.IMG_DOWNLOAD_METHOD == "qt":
            url = QtCore.QUrl.fromUserInput(imageUri)
            # TODO handle cache of images ?
            # TODO handle image resize when ui resize
            self.imgDownloader.start_download(url)
        elif config.IMG_DOWNLOAD_METHOD == "direct":
            # TODO Thread that ?
            image = QtGui.QImage(getCardImageFromUrl(imageUri, cardId))
            self.displayPixmapCard(image)

        # scrifall uri
        try:
            self.scryfallUriLabel.setText(f"<a href={self.card['related_uris']['gatherer']}>Gatherer Link</a>")
        except KeyError:
            self.scryfallUriLabel.setText(f"<a href={self.card['scryfall_uri']}>Scryfall Link</a>")
        self.scryfallUriLabel.linkActivated.disconnect(self.on_scryfallLinkClicked)
        self.scryfallUriLabel.linkActivated.connect(self.on_scryfallLinkClicked)

        # price
        self.avgPriceLabel.setText(
            str(utils.getFromDict(self.card, ["prices", constants.CURRENCY[0]])) + " " + constants.CURRENCY[1]
        )

    def on_setChange(self):
        selectedSet = self.setSelect.itemData(self.setSelect.currentIndex())
        self.display(scryfall.getCardReprintId(self.card["id"], selectedSet))


class ImageDownloader(QtCore.QObject):
    finished = QtCore.Signal(QtGui.QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.finished.connect(self.handle_finished)

    def start_download(self, url):
        self.manager.get(QtNetwork.QNetworkRequest(url))

    def handle_finished(self, reply):
        if reply.error() != QtNetwork.QNetworkReply.NoError:
            print("error: ", reply.errorString())
            return
        image = QtGui.QImage()
        image.loadFromData(reply.readAll())
        self.finished.emit(image)


def getCardImageFromUrl(url, cardId) -> str:
    cardImgPath = Path("resources/images/cards/") / cardId
    if not (cardImgPath.is_file() and os.access(cardImgPath, os.R_OK)):
        urllib.request.urlretrieve(url, cardImgPath)
    return cardImgPath
