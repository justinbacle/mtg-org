import sys
from pathlib import Path

from PySide6 import QtWidgets, QtCore, QtGui
import qt_material

from widgets.cardviewer import CardViewer
from widgets.deckselector import CardStackSelector
from widgets.dbbrowser import DbBrowser
from widgets.cardslist import CardsList

import connector

from lib import qt, utils
import config


class MTGORG_GUI(QtWidgets.QMainWindow):
    app = QtWidgets.QApplication(['', '--no-sandbox'])

    def __init__(self, parent=None):
        super().__init__(parent)

        if config.THEME == "material":
            qt_material.apply_stylesheet(self.app, theme='dark_teal.xml', extra={'density_scale': '-1'})

        self.app.setWindowIcon(QtGui.QIcon(Path("resources/icons/mirari.png").as_posix()))
        self.setWindowTitle("MTGorg")
        if utils.isWin():
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'mtgorg.mainwindow')

        if config.THEME == "fusion":
            qt.selectPalette(self.app)

        # Set Font
        self.manaFontId = QtGui.QFontDatabase.addApplicationFont("resources/fonts/mana/mana.ttf")  # Mana font
        self.ndpmtgFontId = QtGui.QFontDatabase.addApplicationFont("resources/fonts/NDPMTG.ttf")  # NDPMTG font (halfs)
        self.keyruneFontId = QtGui.QFontDatabase.addApplicationFont("resources/fonts/keyrune/keyrune.ttf")  # Set font

        # Load frontend
        self.setupUi()

    def setupUi(self):
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QtWidgets.QHBoxLayout(self.centralWidget)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self.centralWidget)
        self.mainLayout.addWidget(self.splitter)

        # Left pane is card viewer
        self.cardViewer = CardViewer(self)
        self.splitter.addWidget(self.cardViewer)

        # Middle Pane are card Browsers
        self.cardBrowsersWidget = QtWidgets.QWidget()
        self.cardBrowsersLayout = QtWidgets.QVBoxLayout()
        self.cardBrowsersWidget.setLayout(self.cardBrowsersLayout)
        self.splitter.addWidget(self.cardBrowsersWidget)
        self.cardBrowsersSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self.cardBrowsersWidget)
        self.cardBrowsersLayout.addWidget(self.cardBrowsersSplitter)

        # Top one is decklist
        self.decklist = CardsList()
        self.decklist.cardSelected.connect(self.on_decklistCardSelected)
        self.cardBrowsersSplitter.addWidget(self.decklist)

        # Bottom one is DB browser
        self.dbBrowser = DbBrowser()
        self.dbBrowser.cardSelected.connect(self.on_dbBrowserCardSelected)
        self.cardBrowsersSplitter.addWidget(self.dbBrowser)

        # Right pane is deck/collection selector
        self.deckSelector = CardStackSelector()
        self.deckSelector.setMaximumWidth(300)
        self.deckSelector.deckSelectionChanged.connect(self.on_cardStackChange)
        self.deckSelector.collectionSelectionChanged.connect(self.on_cardStackChange)
        self.splitter.addWidget(self.deckSelector)

    def on_decklistCardSelected(self, cardId: str):
        self.dbBrowser.dbResultsList.clearSelection()
        self.cardViewer.display(cardId)

    def on_dbBrowserCardSelected(self, cardId: str):
        self.decklist.cardsList.clearSelection()
        self.cardViewer.display(cardId)

    def on_cardStackChange(self, cardStack: connector.Deck | connector.Collection):
        self.decklist.cardsList.setCardList(cardStack["cardList"])


if __name__ == '__main__':
    window = MTGORG_GUI()
    window.showMaximized()
    sys.exit(window.app.exec())
