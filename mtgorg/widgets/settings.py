import logging

from PySide6 import QtCore, QtWidgets

import config
import constants
import connector
from lib import bulk, scryfall


def downloadBulkDataWithProgress(parent: QtWidgets.QWidget, manager: bulk.BulkDataManager) -> bool:
    progress = QtWidgets.QProgressDialog(
        f"Downloading Scryfall bulk data ({manager.bulkType})...",
        "Cancel",
        0,
        0,
        parent,
    )
    progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)

    def progressCallback(downloadedBytes: int, totalBytes: int) -> bool:
        if totalBytes > 0:
            if progress.maximum() != totalBytes:
                progress.setMaximum(totalBytes)
            progress.setValue(downloadedBytes)
        QtWidgets.QApplication.processEvents()
        return not progress.wasCanceled()

    try:
        manager.downloadBulkData(progress_callback=progressCallback)
    except bulk.DownloadCancelled:
        logging.info("Bulk data download cancelled")
        return False
    except Exception as e:
        logging.error(f"Bulk data download failed: {e}")
        QtWidgets.QMessageBox.critical(parent, "Bulk download failed", str(e))
        return False
    finally:
        progress.close()
    return True


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(620)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.scryfallGroup = QtWidgets.QGroupBox("Scryfall")
        self.scryfallLayout = QtWidgets.QFormLayout()
        self.scryfallGroup.setLayout(self.scryfallLayout)
        self.mainLayout.addWidget(self.scryfallGroup)

        self.useBulkCB = QtWidgets.QCheckBox("Use offline bulk data (card data only; images stay online)")
        self.scryfallLayout.addRow(self.useBulkCB)

        self.languageCB = QtWidgets.QComboBox()
        self.languageCB.addItem("English (default_cards)", "english")
        self.languageCB.addItem("All languages (all_cards)", "all")
        self.scryfallLayout.addRow("Bulk language coverage", self.languageCB)

        self.autoUpdateCB = QtWidgets.QCheckBox("Check for and offer bulk-data updates on startup")
        self.scryfallLayout.addRow(self.autoUpdateCB)

        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.statusLabel.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.scryfallLayout.addRow(self.statusLabel)

        self.downloadPB = QtWidgets.QPushButton("Download / Update now")
        self.downloadPB.clicked.connect(self.on_downloadClicked)
        self.scryfallLayout.addRow(self.downloadPB)

        self.cacheGroup = QtWidgets.QGroupBox("Cache")
        self.cacheLayout = QtWidgets.QVBoxLayout()
        self.cacheGroup.setLayout(self.cacheLayout)
        self.mainLayout.addWidget(self.cacheGroup)

        self.cacheLabel = QtWidgets.QLabel(
            "Cached card data, card images, set icons, and set metadata. "
            "Decks and collections are not affected."
        )
        self.cacheLabel.setWordWrap(True)
        self.cacheLayout.addWidget(self.cacheLabel)

        self.clearCachePB = QtWidgets.QPushButton("Clear cache")
        self.clearCachePB.clicked.connect(self.on_clearCacheClicked)
        self.cacheLayout.addWidget(self.clearCachePB)

        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)

        self.loadSettings()
        self.useBulkCB.toggled.connect(self.updateControls)
        self.languageCB.currentIndexChanged.connect(self.updateControls)
        self.updateControls()

    def loadSettings(self):
        settings = config.getScryfallSettings()
        self.useBulkCB.setChecked(settings["use_bulk_files"])
        self.autoUpdateCB.setChecked(settings["bulk_auto_update"])
        languageIndex = self.languageCB.findData(settings["bulk_language_mode"])
        self.languageCB.setCurrentIndex(max(languageIndex, 0))

    def manager(self) -> bulk.BulkDataManager:
        languageMode = self.languageCB.currentData()
        bulkType = bulk.BulkDataManager.getBulkTypeForMode(languageMode)
        return bulk.BulkDataManager(bulkType=bulkType)

    def updateControls(self):
        enabled = self.useBulkCB.isChecked()
        self.languageCB.setEnabled(enabled)
        self.autoUpdateCB.setEnabled(enabled)
        self.downloadPB.setEnabled(enabled)
        self.updateStatus()

    def updateStatus(self):
        status = self.manager().getStatus()
        if status["local_path"] is None:
            self.statusLabel.setText("No bulk file downloaded for this mode.")
            self.downloadPB.setText("Download now")
            return
        sizeMb = status["size"] / (1024 * 1024)
        updatedAt = status["updated_at"] or "unknown"
        self.statusLabel.setText(
            f"{status['local_path'].name}\n"
            f"{sizeMb:.1f} MB - data updated {updatedAt}"
        )
        self.downloadPB.setText("Update now")

    def on_clearCacheClicked(self):
        answer = QtWidgets.QMessageBox.question(
            self,
            "Clear cache",
            "Delete cached card data, card images, set icons, and set metadata?\n"
            "Your decks and collections will not be affected.",
        )
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        stats = connector.clearCache()
        scryfall.resetSetsCache()
        scryfall.resetFormatsCache()
        if stats["errors"]:
            QtWidgets.QMessageBox.warning(
                self,
                "Cache partially cleared",
                f"Cleared {stats['files']} file(s), but some files could not be removed.",
            )
            return
        sizeMb = stats["bytes"] / (1024 * 1024)
        QtWidgets.QMessageBox.information(
            self,
            "Cache cleared",
            f"Cleared {stats['files']} file(s), {sizeMb:.1f} MB.",
        )

    def on_downloadClicked(self):
        manager = self.manager()
        if not downloadBulkDataWithProgress(self, manager):
            return
        scryfall.resetBulkDataCache()
        scryfall.resetSetsCache()
        scryfall.resetFormatsCache()
        self.updateStatus()

    def accept(self):
        useBulkFiles = self.useBulkCB.isChecked()
        autoUpdate = self.autoUpdateCB.isChecked()
        languageMode = self.languageCB.currentData()
        manager = self.manager()

        if useBulkFiles and manager.getLocalBulkFile() is None:
            answer = QtWidgets.QMessageBox.question(
                self,
                "Bulk data missing",
                "No bulk file is downloaded for this mode. Download it now?",
            )
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                if not downloadBulkDataWithProgress(self, manager):
                    return

        config.saveScryfallSettings(useBulkFiles, autoUpdate, languageMode)
        config.loadScryfallSettings()
        if constants.USE_BULK_FILES and manager.getLocalBulkFile() is None:
            logging.warning("Bulk data missing, using online-only mode for this session")
            constants.USE_BULK_FILES = False
        scryfall.resetBulkDataCache()
        scryfall.resetSetsCache()
        scryfall.resetFormatsCache()
        super().accept()
