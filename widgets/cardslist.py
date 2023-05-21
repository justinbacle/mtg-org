from PySide6 import QtWidgets

from widgets.cardlistwidget import CardListWidget


class CardsList(QtWidgets.QWidget):
    # To Build
    # Display currently selected deck/collection
    def __init__(self, parent=None, **kwargs):
        super(CardsList, self).__init__(parent=parent, **kwargs)

        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        # Left (main pane) is cards list
        self.cardsList = CardListWidget()
        self.mainLayout.addWidget(self.cardsList)

        # Right pane is infos data (text, graphs, list, ...)
        self.infoPanel = InfoWidget()
        self.mainLayout.addWidget(self.infoPanel)


class InfoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
