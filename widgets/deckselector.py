from PySide6 import QtWidgets, QtCore

import connector


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
        self.layout.addWidget(self.splitter)

        # Collections
        self.collectionsWidget = QtWidgets.QWidget()
        self.collectionsWidgetLayout = QtWidgets.QVBoxLayout(self.collectionsWidget)
        self.collectionsLabel = QtWidgets.QLabel("Collections")
        self.collectionsWidgetLayout.addWidget(self.collectionsLabel)
        self.collectionsListWidget = QtWidgets.QListWidget()
        self.collectionsWidgetLayout.addWidget(self.collectionsListWidget)

        self.collectionEditionLayout = QtWidgets.QHBoxLayout()
        self.collectionsWidgetLayout.addLayout(self.collectionEditionLayout)
        self.addCollectionPB = QtWidgets.QPushButton("+")
        self.addCollectionPB.clicked.connect(self.on_addColl)
        self.collectionEditionLayout.addWidget(self.addCollectionPB)
        self.removeCollectionPB = QtWidgets.QPushButton("-")
        self.removeCollectionPB.clicked.connect(self.on_removeColl)
        self.collectionEditionLayout.addWidget(self.removeCollectionPB)
        self.editCollectionPB = QtWidgets.QPushButton("...")
        self.editCollectionPB.clicked.connect(self.on_editColl)
        self.collectionEditionLayout.addWidget(self.editCollectionPB)

        self.splitter.addWidget(self.collectionsWidget)

        # Decks
        self.decksWidget = QtWidgets.QWidget()
        self.decksWidgetLayout = QtWidgets.QVBoxLayout(self.decksWidget)
        self.decksLabel = QtWidgets.QLabel("Decks")
        self.decksWidgetLayout.addWidget(self.decksLabel)
        self.decksListWidget = QtWidgets.QListWidget()
        self.decksWidgetLayout.addWidget(self.decksListWidget)
        self.splitter.addWidget(self.decksWidget)

        self.deckEditionLayout = QtWidgets.QHBoxLayout()
        self.decksWidgetLayout.addLayout(self.deckEditionLayout)
        self.addDeckPB = QtWidgets.QPushButton("+")
        self.addDeckPB.clicked.connect(self.on_addDeck)
        self.deckEditionLayout.addWidget(self.addDeckPB)
        self.removeDeckPB = QtWidgets.QPushButton("-")
        self.removeDeckPB.clicked.connect(self.on_removeDeck)
        self.deckEditionLayout.addWidget(self.removeDeckPB)
        self.editDeckPB = QtWidgets.QPushButton("...")
        self.editDeckPB.clicked.connect(self.on_editDeck)
        self.deckEditionLayout.addWidget(self.editDeckPB)

    def on_addColl(self):
        collName, ok = QtWidgets.QInputDialog.getText(
            self, "QInputDialog.getText()",
            "New collection name:", QtWidgets.QLineEdit.Normal,
        )
        if ok and collName:
            connector.createCollection(collName)
            self.initData()

    def on_removeColl(self):
        button = QtWidgets.QMessageBox.question(
            self, "Confirm deletion ?", "This will permanently delete the collection and its contents, continue ?")
        if button == QtWidgets.QMessageBox.Yes:
            connector.removeCollection(self.getSelected()[1])
            self.initData()

    def on_editColl(self):
        # TODO
        ...

    def on_addDeck(self):
        deckName, ok = QtWidgets.QInputDialog.getText(
            self, "QInputDialog.getText()",
            "New deck name:", QtWidgets.QLineEdit.Normal,
        )
        if ok and deckName:
            connector.createDeck(deckName)
            self.initData()

    def on_removeDeck(self):
        button = QtWidgets.QMessageBox.question(
            self, "Confirm deletion ?", "This will permanently delete the deck and its contents, continue ?")
        if button == QtWidgets.QMessageBox.Yes:
            connector.removeDeck(self.getSelected()[1])
            self.initData()

    def on_editDeck(self):
        # TODO
        ...

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
        self.collectionsListWidget.clear()
        for collection in collectionsList:
            # TODO add more data ?
            self.collectionsListWidget.addItem(collectionItem(collection["name"]))

        # Decks
        decksList = connector.getDecksList()
        self.decksListWidget.clear()
        for deck in decksList:
            self.decksListWidget.addItem(collectionItem(deck["name"]))


def collectionItem(collectionName) -> QtWidgets.QListWidgetItem:
    return QtWidgets.QListWidgetItem(collectionName)
