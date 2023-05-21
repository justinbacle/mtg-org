from PySide6 import QtWidgets, QtCore

from widgets.cardlistwidget import CardListWidget


class DbBrowser(QtWidgets.QWidget):
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
        ...

    def on_dbSelectChanged(self, selectedItem):
        # TODO emit signal to the card viewer to display selected card
        ...


class SearchForm(QtWidgets.QWidget):

    find: QtCore.Signal = QtCore.Signal(dict)   # ? replace with search dict object ?

    # To Build
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
