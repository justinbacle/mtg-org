from PySide6 import QtWidgets, QtCore

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from lib import scryfall  # noqa E402
from widgets.cardlistwidget import CardListWidget  # noqa E402


class DbBrowser(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # To Build
    def __init__(self, parent=None, **kwargs):
        super(DbBrowser, self).__init__(parent=parent, **kwargs)

        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)
        # Form on the left for search terms ?
        self.searchForm = SearchForm()
        self.searchForm.find.connect(self.on_searchRequest)
        self.mainLayout.addWidget(self.searchForm)
        # QListWidget on the right for results
        self.dbResultsList = CardListWidget()
        self.dbResultsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.mainLayout.addWidget(self.dbResultsList)

    def on_searchRequest(self, searchDict: dict):
        # TODO update list with results
        req = [scryfall.getCardByName(searchDict["name"])]  # TODO remove
        self.dbResultsList.clear()
        self.dbResultsList.setData(req)

    def on_dbSelectChanged(self):
        if len(self.dbResultsList.selectedItems()) == 1:
            selectedItem = self.dbResultsList.selectedItems()[0]
        else:
            selectedItem = None
        self.cardSelected.emit(selectedItem.data(QtCore.Qt.UserRole)["id"])


class SearchForm(QtWidgets.QWidget):

    find: QtCore.Signal = QtCore.Signal(dict)   # ? replace with search dict object ?

    # To Build
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.mainLayout = QtWidgets.QFormLayout()
        self.setLayout(self.mainLayout)

        self.nameField = QtWidgets.QLineEdit()
        self.mainLayout.addRow("Name", self.nameField)

        self.searchButton = QtWidgets.QPushButton("Search")
        self.searchButton.clicked.connect(self.on_searchAction)
        self.mainLayout.addWidget(self.searchButton)

    def on_searchAction(self):
        self.find.emit(self.getSearchData())

    def getSearchData(self):
        searchData = {
            "name": self.nameField.text()
        }
        return searchData
