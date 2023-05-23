from PySide6 import QtWidgets, QtCore

import connector

import constants


class CardStackSelector(QtWidgets.QWidget):

    # Signals
    deckSelectionChanged: QtCore.Signal = QtCore.Signal(connector.Deck)
    collectionSelectionChanged: QtCore.Signal = QtCore.Signal(connector.Collection)

    def __init__(self, parent=None, **kwargs):
        super(CardStackSelector, self).__init__(parent=parent, **kwargs)

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

    def getSelected(self):
        if len(self.decksListWidget.selectedItems()) == 1:
            stackType = "deck"
            stackName = self.decksListWidget.selectedItems()[0].text()
        elif len(self.collectionsListWidget.selectedItems()) == 1:
            stackType = "collection"
            stackName = self.collectionsListWidget.selectedItems()[0].text()
        else:
            stackType = None
            stackName = None
        return (stackType, stackName)

    def setCallBacks(self):
        self.collectionsListWidget.itemSelectionChanged.connect(self.on_collectionSelectChanged)
        self.decksListWidget.itemSelectionChanged.connect(self.on_deckSelectChanged)

    def on_collectionSelectChanged(self):
        if len(self.collectionsListWidget.selectedItems()) == 1:
            collectionName = self.collectionsListWidget.selectedItems()[0].text()
            collection = connector.getCollection(collectionName)
            self.collectionSelectionChanged.emit(collection)
            self.decksListWidget.clearSelection()

    def on_deckSelectChanged(self):
        if len(self.decksListWidget.selectedItems()) == 1:
            deckName = self.decksListWidget.selectedItems()[0].text()
            deck = connector.getDeck(deckName)
            self.deckSelectionChanged.emit(deck)
            self.collectionsListWidget.clearSelection()

    def initData(self):
        # Collections
        collectionsList = connector.getCollectionsList()

        for collection in collectionsList:
            # TODO add more data ?
            self.collectionsListWidget.addItem(collectionItem(collection["name"]))

        # Decks
        decksList = connector.getDecksList()

        for deck in decksList:
            self.decksListWidget.addItem(collectionItem(deck["name"]))


def collectionItem(collectionName) -> QtWidgets.QListWidgetItem:
    return QtWidgets.QListWidgetItem(collectionName)
