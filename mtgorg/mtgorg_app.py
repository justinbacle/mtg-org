import os
import sys
import logging
from pathlib import Path
import datetime

from PySide6 import QtWidgets, QtCore, QtGui
import qt_material

from widgets.cardviewer import CardViewer
from widgets.deckselector import CardStackSelector
from widgets.dbbrowser import DbBrowser
from widgets.cardslist import CardsList

import connector
import config
import constants

from lib import qt, utils


class MTGORG_GUI(QtWidgets.QMainWindow):
    app = QtWidgets.QApplication(['', '--no-sandbox'])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.statusbar = QtWidgets.QStatusBar()

        def on_log(record: logging.LogRecord):
            timeStr = datetime.datetime.now().strftime("%H:%M:%S")
            logMsg = f"[{timeStr}] {record.levelname}: {record.msg} ({record.filename}:{record.lineno})"
            # ? show log level with color with self.statusbar.setStyleSheet
            self.statusbar.showMessage(logMsg)

        logging.getLogger().addFilter(on_log)

        self.setStatusBar(self.statusbar)

        if constants.THEME == "material":
            qt_material.apply_stylesheet(self.app, theme='dark_teal.xml', extra={'density_scale': '0'})

        # FIXME: not working on KDE ubuntu, only seeing wayland's "W" icon
        # ? see : https://doc.qt.io/qtforpython-6/overviews/appicon.html
        iconPath = Path("resources/icons/mirari.png").as_posix()
        icon = QtGui.QIcon()
        icon.addFile(iconPath)
        self.app.setWindowIcon(icon)

        self.setWindowTitle("MTG Organizer")
        if utils.isWin():
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'mtgorg.mainwindow')
        elif utils.isLinux():
            # Not needed ?
            ...
        elif utils.isMac():
            # ? Who cares ?
            ...
        else:
            logging.error("Unhandled system platform")
            ...

        if constants.THEME == "fusion":
            qt.selectPalette(self.app)

        # Update resources
        self.initSettings()
        self.initUserFolders()
        self.updateResources()

        # Set Font
        KEYRUNE_FONT_PATH = constants.DEFAULT_FONTS_LOCATION / "keyrune.ttf"
        self.keyruneFontId = QtGui.QFontDatabase.addApplicationFont(KEYRUNE_FONT_PATH.as_posix())  # Set font
        PROXYGLYPH_FONT_PATH = constants.DEFAULT_FONTS_LOCATION / "Proxyglyph.ttf"
        self.proxyglyphFontId = QtGui.QFontDatabase.addApplicationFont(PROXYGLYPH_FONT_PATH.as_posix())  # better NDPMTG
        # from scryfall website
        PHYREXIAN_FONT_PATH = Path("resources/fonts/Phyrexian-Regular.woff2")
        self.phyrexianFontId = QtGui.QFontDatabase.addApplicationFont(PHYREXIAN_FONT_PATH.as_posix())  # Phyrexian cards

        # Load frontend
        self.setupUi()

    def initSettings(self):
        if not config.configFileExists():
            config.createConfigFile()

    def initUserFolders(self):
        userFolders = [
            constants.DEFAULT_ROOT_USER_FOLDER,
            constants.DEFAULT_BULK_FOLDER_LOCATION,
            constants.DEFAULT_INFOS_LOCATION,
            constants.DEFAULT_FONTS_LOCATION,
            constants.DEFAULT_SET_ICONS_LOCATION,
            constants.DEFAULT_CARDIMAGES_LOCATION
        ]
        for userFolder in userFolders:
            if not userFolder.is_dir():
                os.makedirs(userFolder)

    def updateResources(self, force: bool = False):
        _configTimeStr = utils.getFromDict(config.readConfig(), ["WEBDATA", "resources_date"])
        if _configTimeStr == "":
            force = True
        else:
            lastUpdateDate = datetime.datetime.strptime(_configTimeStr, constants.DATETIME_FORMAT)
            if (datetime.datetime.now() - lastUpdateDate) > datetime.timedelta(7):
                force = True
        # Keyrune (set icons)
        KEYRUNE_FONT_FILEPATH = constants.DEFAULT_FONTS_LOCATION / "keyrune.ttf"
        _updated = False
        if force or not KEYRUNE_FONT_FILEPATH.is_file():
            keyruneFontUrl = "https://github.com/andrewgioia/keyrune/raw/master/fonts/keyrune.ttf"
            utils.downloadFileFromUrl(keyruneFontUrl, KEYRUNE_FONT_FILEPATH)
            _updated = True
        KEYRUNE_EQU_FILE = constants.DEFAULT_FONTS_LOCATION / "keyrune.json"
        if force or not KEYRUNE_EQU_FILE.is_file():
            utils.updateKeyRuneSymbols()
            _updated = True
        # Proxygliyph (better npdmtg)
        PROXYGLIYPH_FONT_FILEPATH = constants.DEFAULT_FONTS_LOCATION / "Proxyglyph.ttf"
        if force or not PROXYGLIYPH_FONT_FILEPATH.is_file():
            proxyglyphFontUrl = "https://github.com/MrTeferi/Proxyshop/raw/main/fonts/Proxyglyph.ttf"
            utils.downloadFileFromUrl(proxyglyphFontUrl, PROXYGLIYPH_FONT_FILEPATH)
            _updated = True
        if _updated:
            config.writeValue(
                datetime.datetime.strftime(datetime.datetime.now(), constants.DATETIME_FORMAT),
                "WEBDATA", "resources_date"
            )
            logging.info("Resources files were updated succesfully")

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
        self.dbBrowser = DbBrowser(parent=self)
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
        if not self.cardViewer.display(cardId):
            self.cardViewer.display(cardId, forceRefresh=True)

    def on_dbBrowserCardSelected(self, cardId: str):
        self.decklist.cardsList.clearSelection()
        if not self.cardViewer.display(cardId):
            self.cardViewer.display(cardId, forceRefresh=True)

    def on_cardStackChange(self, cardStack: connector.Deck | connector.Collection):
        if cardStack is not None:
            self.decklist.cardsList.setCardList(cardStack["cardList"])
        else:
            self.decklist.cardsList.clear()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    window = MTGORG_GUI()
    window.showMaximized()
    sys.exit(window.app.exec())
