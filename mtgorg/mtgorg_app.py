import os
import sys
import logging
import threading
import datetime

from PySide6 import QtWidgets, QtCore, QtGui
import qt_material

from widgets.cardviewer import CardViewer
from widgets.deckselector import CardStackSelector
from widgets.dbbrowser import DbBrowser
from widgets.cardslist import CardsList
from widgets.settings import SettingsDialog, downloadBulkDataWithProgress, ensureBulkCacheWithProgress
from widgets.logviewer import ClickableStatusBar, LogHistoryHandler, LogViewerDialog
from widgets.onboarding import OnboardingWizard

import connector
import config
import constants

from lib import bulk, datarefresh, qt, scryfall, updates, utils


class MTGORG_GUI(QtWidgets.QMainWindow):
    app = QtWidgets.QApplication(['', '--no-sandbox'])
    logMessage = QtCore.Signal(str)
    setRefreshFinished = QtCore.Signal(bool)
    updateAvailable = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._systemPalette = self.app.palette()

        self.statusbar = ClickableStatusBar()
        self.statusbar.setToolTip("Click to view the full log")
        self.statusbar.clicked.connect(self.on_showLogs)
        self.logMessage.connect(self.statusbar.showMessage)
        self.setRefreshFinished.connect(self.onSetRefreshFinished)
        self.updateAvailable.connect(self.onUpdateAvailable)
        self._setRefreshRunning = False

        self.logHistory = LogHistoryHandler()
        self.logHistory.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S")
        )

        def on_log(record: logging.LogRecord) -> bool:
            timeStr = datetime.datetime.now().strftime("%H:%M:%S")
            logMsg = f"[{timeStr}] {record.levelname}: {record.getMessage()} ({record.filename}:{record.lineno})"
            self.logMessage.emit(logMsg)
            return True

        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.INFO)
        rootLogger.addHandler(self.logHistory)
        rootLogger.addFilter(on_log)

        self.setStatusBar(self.statusbar)

        self.initUserFolders()
        self.initSettings()
        self._onboarding = self.runOnboarding()
        self.applyTheme()

        # FIXME: not working on KDE ubuntu, only seeing wayland's "W" icon
        # ? see : https://doc.qt.io/qtforpython-6/overviews/appicon.html
        iconPath = constants.resourcePath("icons", "mirari.png").as_posix()
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

        # Update resources
        self.updateResources()

        # Set Font
        KEYRUNE_FONT_PATH = constants.DEFAULT_FONTS_LOCATION / "keyrune.ttf"
        self.keyruneFontId = QtGui.QFontDatabase.addApplicationFont(KEYRUNE_FONT_PATH.as_posix())  # Set font
        PROXYGLYPH_FONT_PATH = constants.DEFAULT_FONTS_LOCATION / "Proxyglyph.ttf"
        self.proxyglyphFontId = QtGui.QFontDatabase.addApplicationFont(PROXYGLYPH_FONT_PATH.as_posix())  # better NDPMTG
        # from scryfall website (TTF converted from woff2 — DirectWrite on Windows cannot load woff2)
        PHYREXIAN_FONT_PATH = constants.resourcePath("fonts", "Phyrexian-Regular.ttf")
        self.phyrexianFontId = QtGui.QFontDatabase.addApplicationFont(PHYREXIAN_FONT_PATH.as_posix())  # Phyrexian cards

        # Load frontend
        self.setupUi()
        self.initShortcuts()
        self._maybeDownloadOnboardingBulk()
        self.initBulkData()

        QtCore.QTimer.singleShot(0, self.startSetRefreshCheck)
        QtCore.QTimer.singleShot(1000, self.startUpdateCheck)
        self.setRefreshTimer = QtCore.QTimer(self)
        self.setRefreshTimer.setInterval(7 * 24 * 60 * 60 * 1000)
        self.setRefreshTimer.timeout.connect(self.startSetRefreshCheck)
        self.setRefreshTimer.start()

    def _showThemeBusy(self):
        if not self.isVisible():
            return None
        busy = QtWidgets.QProgressDialog("Applying theme...", None, 0, 0, self)
        busy.setWindowTitle("Theme")
        busy.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        busy.setMinimumDuration(0)
        busy.setAutoClose(False)
        busy.show()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        QtWidgets.QApplication.processEvents()
        return busy

    def applyTheme(self):
        busy = self._showThemeBusy()
        if busy is None:
            self._applyTheme()
            return
        # Let the modal indicator paint before the stylesheet repolish blocks the GUI thread.
        QtCore.QTimer.singleShot(50, lambda: self._finishThemeApply(busy))

    def _finishThemeApply(self, busy):
        try:
            self._applyTheme()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            busy.close()
            QtWidgets.QApplication.processEvents()

    def _applyTheme(self):
        if constants.THEME == "material":
            themeFile = "dark_teal.xml" if qt.systemPrefersDark() else "light_teal.xml"
            qt_material.apply_stylesheet(self.app, theme=themeFile, extra={'density_scale': '0'})
            self.app.setStyleSheet(self.app.styleSheet() + """
QComboBox::item:selected,
QComboBox QAbstractItemView::item:selected {
    color: #232629;
    background-color: #6effe8;
}
QMenu::item:selected {
    color: #232629;
    background-color: #6effe8;
}
""")
        elif constants.THEME == "kde":
            qt.applySystemTheme(self.app, self._systemPalette)
        else:
            qt.applyFusionTheme(self.app)
        if hasattr(self, "decklist"):
            self.decklist.applyTheme()
        if hasattr(self, "deckSelector"):
            self.deckSelector.applyTheme()

    def startSetRefreshCheck(self):
        """Check for a new Scryfall set without blocking the UI."""
        if constants.USE_BULK_FILES or self._setRefreshRunning:
            return
        self._setRefreshRunning = True
        threading.Thread(target=self._checkForNewSets, daemon=True).start()

    def _checkForNewSets(self):
        updated = False
        try:
            updated = datarefresh.checkForUpdates().updated
            if not updated:
                logging.info("Scryfall set data is up to date")
        except Exception as e:
            logging.warning(f"Could not check for new Scryfall sets: {e}")
        finally:
            self._setRefreshRunning = False
            self.setRefreshFinished.emit(updated)

    def onSetRefreshFinished(self, updated: bool):
        if updated:
            self.refreshDataSources()

    def on_showLogs(self):
        LogViewerDialog(self.logHistory, self).exec()

    def initSettings(self):
        if not config.configFileExists():
            config.createConfigFile()
        config.loadScryfallSettings()
        config.loadSearchSettings()
        config.loadUISettings()
        config.loadUpdateSettings()

    def runOnboarding(self):
        if config.getUISettings()["onboarding_done"]:
            return None
        wizard = OnboardingWizard()
        accepted = wizard.exec() == QtWidgets.QDialog.DialogCode.Accepted
        values = wizard.values() if accepted else {
            "use_bulk": constants.USE_BULK_FILES,
            "bulk_language": constants.BULK_LANGUAGE_MODE,
            "download_bulk": False,
            "theme": constants.THEME,
            "check_updates": constants.AUTO_CHECK_UPDATES,
        }
        config.saveUISettings(values["theme"], onboardingDone=True)
        config.saveScryfallSettings(values["use_bulk"], True, values["bulk_language"])
        config.saveUpdateSettings(values["check_updates"])
        config.loadUISettings()
        config.loadScryfallSettings()
        config.loadUpdateSettings()
        return values

    def _maybeDownloadOnboardingBulk(self):
        if not self._onboarding or not self._onboarding.get("download_bulk"):
            return
        manager = bulk.BulkDataManager()
        if manager.getLocalBulkFile() is not None:
            return
        if downloadBulkDataWithProgress(self, manager):
            ensureBulkCacheWithProgress(self)

    def startUpdateCheck(self):
        if not constants.AUTO_CHECK_UPDATES:
            return
        threading.Thread(target=self._checkForUpdates, daemon=True).start()

    def _checkForUpdates(self):
        try:
            result = updates.checkForUpdate()
        except Exception as e:
            logging.warning(f"Could not check for updates: {e}")
            return
        if result is not None:
            self.updateAvailable.emit(result)

    def onUpdateAvailable(self, result: dict):
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("Update available")
        box.setText(f"MTG Organizer {result['version']} is available.")
        box.setInformativeText("Open the GitHub release to download the new version.")
        openButton = box.addButton("Open release", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        skipButton = box.addButton("Skip this version", QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Later", QtWidgets.QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is openButton and result.get("url"):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(result["url"]))
        elif box.clickedButton() is skipButton:
            config.saveUpdateSettings(constants.AUTO_CHECK_UPDATES, skippedVersion=result["version"])

    def initShortcuts(self):
        settingsAction = QtGui.QAction(self)
        settingsAction.setShortcut(QtGui.QKeySequence("Ctrl+,"))
        settingsAction.triggered.connect(self.on_settingsRequested)
        self.addAction(settingsAction)

    def on_settingsRequested(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.refreshDataSources()

    def refreshDataSources(self):
        try:
            self.dbBrowser.searchForm.refreshDataSources()
        except Exception as e:
            logging.error(f"Could not refresh search data sources: {e}")

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
        connector.getCacheDB()

    def initBulkData(self):
        if not constants.USE_BULK_FILES:
            return
        manager = bulk.BulkDataManager()
        if manager.getLocalBulkFile() is None:
            answer = QtWidgets.QMessageBox.question(
                self,
                "Scryfall bulk data",
                "Offline bulk data is enabled but no file is downloaded.\n"
                "Download it now (about 80 MB compressed for English, more for all languages)?",
            )
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                logging.warning("Bulk data unavailable, using online-only mode for this session")
                constants.USE_BULK_FILES = False
                return
            if not downloadBulkDataWithProgress(self, manager):
                logging.warning("Bulk data download failed, using online-only mode for this session")
                constants.USE_BULK_FILES = False
                return
        elif constants.BULK_AUTO_UPDATE:
            try:
                updateAvailable = manager.needsUpdate()
            except Exception as e:
                logging.warning(f"Could not check for bulk data updates: {e}")
                updateAvailable = False
            if updateAvailable:
                answer = QtWidgets.QMessageBox.question(
                    self,
                    "Scryfall bulk data",
                    "A newer bulk-data file is available. Download it now?",
                )
                if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                    if not downloadBulkDataWithProgress(self, manager):
                        logging.warning("Bulk data update failed, keeping the existing file")
        if not ensureBulkCacheWithProgress(self):
            logging.error("Bulk data could not be loaded")
            answer = QtWidgets.QMessageBox.question(
                self,
                "Scryfall bulk data",
                "The local bulk file could not be loaded. Re-download it now?",
            )
            if answer == QtWidgets.QMessageBox.StandardButton.Yes and downloadBulkDataWithProgress(self, manager):
                scryfall.resetBulkDataCache()
                if not ensureBulkCacheWithProgress(self):
                    logging.error("Bulk data still could not be loaded")
                    constants.USE_BULK_FILES = False
                    logging.warning("Using online-only mode for this session")
            else:
                constants.USE_BULK_FILES = False
                logging.warning("Using online-only mode for this session")

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
        else:
            try:
                keyRuneMtime = KEYRUNE_EQU_FILE.stat().st_mtime
                setCodes = [setData["code"] for setData in scryfall.getSets()]
                missing = utils.updateKeyRuneIfMissing(setCodes)
                if KEYRUNE_EQU_FILE.stat().st_mtime > keyRuneMtime:
                    _updated = True
                if missing:
                    logging.info(f"Keyrune still has no icon for: {', '.join(missing[:10])}")
            except Exception as e:
                logging.warning(f"Could not check for missing Keyrune icons: {e}")
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
        self._centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self._centralWidget)
        self.mainLayout = QtWidgets.QHBoxLayout(self._centralWidget)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self._centralWidget)
        qt.configureSplitter(self.splitter)
        self.mainLayout.addWidget(self.splitter)

        # Left pane is card viewer
        self.cardViewer = CardViewer(self)
        self.cardViewer.replaceInDeckRequested.connect(self.on_replaceCardInDeck)
        self.splitter.addWidget(self.cardViewer)

        # Middle Pane are card Browsers
        self.cardBrowsersWidget = QtWidgets.QWidget()
        self.cardBrowsersLayout = QtWidgets.QVBoxLayout()
        self.cardBrowsersWidget.setLayout(self.cardBrowsersLayout)
        self.splitter.addWidget(self.cardBrowsersWidget)
        self.cardBrowsersSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical, self.cardBrowsersWidget)
        qt.configureSplitter(self.cardBrowsersSplitter)
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
        self.deckSelector.settingsRequested.connect(self.on_settingsRequested)
        self.splitter.addWidget(self.deckSelector)

    def on_decklistCardSelected(self, cardId: str):
        self.dbBrowser.dbResultsList.clearSelection()
        self.cardViewer.display_from_deck(cardId)

    def on_dbBrowserCardSelected(self, cardId: str):
        self.decklist.cardsList.clearSelection()
        self.cardViewer.display_from_db(cardId)

    def on_replaceCardInDeck(self, oldCardId: str, newCardId: str):
        self.decklist.replaceCardInAnySection(oldCardId, newCardId)

    def on_cardStackChange(self, cardStack: connector.Deck | connector.Collection):
        if cardStack is not None:
            stackType, stackName = self.deckSelector.getSelected()
            self.decklist.setCardStack(cardStack, stackType, stackName)
        else:
            self.decklist.cardsList.clear()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    window = MTGORG_GUI()
    window.showMaximized()
    sys.exit(window.app.exec())
