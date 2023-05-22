from PySide6 import QtWidgets, QtGui, QtCore, QtNetwork, QtSvgWidgets

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from lib import scryfall, utils  # noqa E402

import constants  # noqa E402


class CardViewer(QtWidgets.QWidget):
    # To Build
    def __init__(self, parent=None, **kwargs):
        super(CardViewer, self).__init__(parent=parent, **kwargs)
        self.setupUi()
        self.imgDownloader = ImageDownloader()
        self.imgDownloader.finished.connect(self.handle_finished)

    def setupUi(self):
        self.mainLayout = QtWidgets.QGridLayout(self)

        # Card Name + Mana
        self.nameLabel = QtWidgets.QLabel("Name")
        self.mainLayout.addWidget(self.nameLabel, 0, 0)
        self.manacostLabel = QtWidgets.QLabel("{M}{A}{N}{A}{0}")
        self.manacostLabel.setFont(QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(0)))
        self.mainLayout.addWidget(self.manacostLabel, 0, 1)

        # Set icon + Name + Year
        self.setIconSvg = QtSvgWidgets.QSvgWidget()
        self.mainLayout.addWidget(self.setIconSvg, 1, 0)
        self.setNameLabel = QtWidgets.QLabel("Set Name")
        self.mainLayout.addWidget(self.setNameLabel, 1, 1)

        # Card Img
        self.cardImgGraphicsView = QtWidgets.QGraphicsView()
        self.mainLayout.addWidget(self.cardImgGraphicsView, 2, 0, 1, 2)

        # Card Link
        self.scryfallUriLabel = QtWidgets.QLabel("uri")
        self.scryfallUriLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.scryfallUriLabel.linkActivated.connect(self.on_scryfallLinkClicked)
        self.mainLayout.addWidget(self.scryfallUriLabel, 3, 0)

    def on_scryfallLinkClicked(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.card['related_uris']['gatherer']))

    def handle_finished(self, image):
        self.cardImgPixMap = QtGui.QPixmap.fromImage(image)
        if self.cardImgGraphicsView.scene() is None:
            self.cardImgGraphicsView.setScene(QtWidgets.QGraphicsScene())
        if any(isinstance(_, QtWidgets.QGraphicsPixmapItem) for _ in self.cardImgGraphicsView.scene().items()):
            self.cardImgGraphicsView.scene().clear()
        self.cardImgGraphicsView.scene().addPixmap(self.cardImgPixMap)
        bounds = self.cardImgGraphicsView.scene().itemsBoundingRect()
        self.cardImgGraphicsView.fitInView(bounds, QtCore.Qt.KeepAspectRatio)
        self.cardImgGraphicsView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.cardImgGraphicsView.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    def display(self, cardId: str):
        self.card = scryfall.getCardById(cardId)
        self.nameLabel.setText(self.card["name"])
        self.manacostLabel.setText(
            setManaText(utils.getFromDict(self.card, ["mana_cost"], ""))
        )
        self.setIconSvg.load(
            scryfall.getSetSvg(self.card["set_id"])
        )
        self.setIconSvg.renderer().setAspectRatioMode(QtCore.Qt.KeepAspectRatio)
        self.setNameLabel.setText(f"{self.card['set_name']} - {scryfall.getSetReleaseDate(self.card['set_id'])}")

        if utils.getFromDict(self.card, ["image_uris"], None) is not None:
            imageUri = utils.getFromDict(
                self.card, ["image_uris", "normal"])
        else:
            # TODO handle two_sided cards -> len(self.card['card_faces']) > 1
            imageUri = utils.getFromDict(
                self.card, ["card_faces", 0, "image_uris", "normal"])

        url = QtCore.QUrl.fromUserInput(imageUri)
        # TODO handle cache of images ?
        # TODO handle image resize when ui resize
        self.imgDownloader.start_download(url)

        # scrifall uri
        self.scryfallUriLabel.setText(f"<a href={self.card['related_uris']['gatherer']}>Scryfall Link</a>")
        self.scryfallUriLabel.linkActivated.connect(self.on_scryfallLinkClicked)


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


def setManaText(inputStr) -> str:
    inputStr.replace("{W}", "&#xe600;")
    inputStr.replace("{U}", "&#xe601;")
    inputStr.replace("{B}", "&#xe602;")
    inputStr.replace("{R}", "&#xe603;")
    inputStr.replace("{G}", "&#xe604;")
    return inputStr
