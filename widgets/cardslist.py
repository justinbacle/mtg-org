from PySide6 import QtWidgets, QtCore

from widgets.cardlistwidget import CardStackListWidget


class CardsList(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # Display currently selected deck/collection
    def __init__(self, parent=None, **kwargs):
        super(CardsList, self).__init__(parent=parent, **kwargs)

        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        # Left (main pane) is cards list
        self.cardsList = CardStackListWidget()
        self.cardsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.mainLayout.addWidget(self.cardsList)

        # Right pane is infos data (text, graphs, list, ...)
        self.infoPanel = InfoWidget()
        self.mainLayout.addWidget(self.infoPanel)

    def on_dbSelectChanged(self):
        if len(self.cardsList.selectedItems()) == 1:
            selectedItem = self.cardsList.selectedItems()[0]
            self.cardSelected.emit(selectedItem.data(QtCore.Qt.UserRole)["id"])
        else:
            selectedItem = None


class InfoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
