from PySide6 import QtWidgets, QtCore

from connector import Collection, Deck

import constants


class DeckSelector(QtWidgets.QWidget):
    # To Build

    # Signals
    deckSelectionChanged: QtCore.Signal = QtCore.Signal(Deck)
    collectionSelectionChanged: QtCore.Signal = QtCore.Signal(Collection)

    def __init__(self, parent=None, **kwargs):
        super(DeckSelector, self).__init__(parent=parent, **kwargs)

        self.initUi()
        self.initData()
        self.setCallBacks()

    def initUi(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        self.splitter.setHandleWidth(constants.QSPLITTER_HANDLE_WIDTH)
        self.layout.addWidget(self.splitter)

        # Collections
        self.collectionsWidget = QtWidgets.QWidget()
        self.collectionsWidgetLayout = QtWidgets.QVBoxLayout(self.collectionsWidget)
        self.collectionsLabel = QtWidgets.QLabel("Collections")
        self.collectionsWidgetLayout.addWidget(self.collectionsLabel)
        self.collectionsListWidget = QtWidgets.QListWidget()
        self.collectionsWidgetLayout.addWidget(self.collectionsListWidget)
        self.splitter.addWidget(self.collectionsWidget)

        # Decks
        self.decksWidget = QtWidgets.QWidget()
        self.decksWidgetLayout = QtWidgets.QVBoxLayout(self.decksWidget)
        self.decksLabel = QtWidgets.QLabel("Decks")
        self.decksWidgetLayout.addWidget(self.decksLabel)
        self.decksListWidget = QtWidgets.QListWidget()
        self.decksWidgetLayout.addWidget(self.decksListWidget)
        self.splitter.addWidget(self.decksWidget)

    def setCallBacks(self):
        self.collectionsListWidget.itemSelectionChanged.connect(self.on_collectionSelectChanged)
        self.decksListWidget.itemSelectionChanged.connect(self.on_deckSelectChanged)

    def on_collectionSelectChanged(self, collection: Collection):
        self.collectionSelectionChanged.emit(collection)

    def on_deckSelectChanged(self, deck: Deck):
        self.deckSelectionChanged.emit(deck)

    def initData(self):
        # TODO get data from db

        # Collections
        # ! Fake Data
        collectionsList = [
            Collection()
        ]

        for collection in collectionsList:
            self.collectionsListWidget.addItem(collectionItem(collection))

        # Decks
        # ! Fake Data
        decksList = [
            Deck()
        ]

        for deck in decksList:
            self.decksListWidget.addItem(collectionItem(deck))


def collectionItem(Collection):
    return QtWidgets.QListWidgetItem(Collection["Name"])
