import sys

from PySide6 import QtWidgets, QtCore

from widgets.cardviewer import CardViewer
from widgets.deckselector import DeckSelector
from widgets.dbbrowser import DbBrowser
from widgets.cardslist import CardsList

from lib import qt
import constants


class MTGORG_GUI(QtWidgets.QMainWindow):
    app = QtWidgets.QApplication(['', '--no-sandbox'])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTheme()

        # Load frontend
        self.setupUi()

    def setupUi(self):
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QtWidgets.QHBoxLayout(self.centralWidget)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self.centralWidget)
        self.splitter.setHandleWidth(constants.QSPLITTER_HANDLE_WIDTH)
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
        self.cardBrowsersSplitter.addWidget(self.decklist)

        # Bottom one is DB browser
        self.dbBrowser = DbBrowser()
        self.cardBrowsersSplitter.addWidget(self.dbBrowser)

        # Right pane is deck/collection selector
        self.deckSelector = DeckSelector()
        self.splitter.addWidget(self.deckSelector)

    def setTheme(self):
        qt.selectPalette(self.app)


if __name__ == '__main__':
    window = MTGORG_GUI()
    window.showMaximized()
    sys.exit(window.app.exec())
