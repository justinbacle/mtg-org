from PySide6 import QtWidgets, QtCore, QtCharts, QtGui

from widgets.cardlistwidget import CardStackListWidget
from lib import utils

import constants


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


class DeckStatsWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.mainLayout = QtWidgets.QGridLayout()
        self.setLayout(self.mainLayout)

        self._cardCountLabel = QtWidgets.QLabel("Card count")
        self.mainLayout.addWidget(self._cardCountLabel, 0, 0)
        self.cardCountLabel = QtWidgets.QLabel()
        self.mainLayout.addWidget(self.cardCountLabel, 0, 1)

        self._totalPriceLabel = QtWidgets.QLabel("Total Price")
        self.mainLayout.addWidget(self._totalPriceLabel, 1, 0)
        self.totalPriceLabel = QtWidgets.QLabel()
        self.mainLayout.addWidget(self.totalPriceLabel, 1, 1)

    def setData(self, dataDict):
        self.cardCountLabel.setText(
            str(dataDict["cardCount"])
        )
        self.totalPriceLabel.setText(
            str(round(dataDict["totalPrice"], 2)) + constants.CURRENCY[1]
        )


class InfoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMaximumWidth(320)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Deck stats
        self.deckStatsWidget = DeckStatsWidget()
        self.mainLayout.addWidget(self.deckStatsWidget)

        # Mana cost
        # Data series
        self.manaBarSeries = QtCharts.QBarSeries()
        self.manaDataSet = QtCharts.QBarSet("Mana Cost")
        self.manaDataSet.append([1, 2, 3, 4, 5, 6, 7])
        self.manaBarSeries.append(self.manaDataSet)
        self.manaBarSeries.append(self.manaDataSet)
        self.manaChart = QtCharts.QChart()
        self.manaChart.setTitle("Mana repartition")
        self.manaChart.addSeries(self.manaBarSeries)
        # Axes
        self.manaCategories = ["0", "1", "2", "3", "4", "5", "6+"]
        self.manaAxisX = QtCharts.QBarCategoryAxis()
        self.manaAxisX.append(self.manaCategories)
        self.manaBarSeries.attachAxis(self.manaAxisX)
        self.manaAxisY = QtCharts.QValueAxis()
        self.manaChart.addAxis(self.manaAxisX, QtCore.Qt.AlignBottom)
        self.manaChart.addAxis(self.manaAxisY, QtCore.Qt.AlignLeft)
        self.manaBarSeries.attachAxis(self.manaAxisY)
        # legend
        self.manaChart.legend().setVisible(False)
        self.manaChart.legend().setAlignment(QtCore.Qt.AlignBottom)
        # View
        self.manaChartView = QtCharts.QChartView(self.manaChart)
        self.manaChartView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.manaChartView.setMinimumSize(160, 160)
        self.mainLayout.addWidget(self.manaChartView)

        # Color repartition
        self.colorPieChart = QtCharts.QChart()
        self.colorPieChart.createDefaultAxes()
        self.colorPieSeries = QtCharts.QPieSeries()
        self.colorPieChart.addSeries(self.colorPieSeries)
        self.colorPieChart.legend().setVisible(False)
        self.colorPieChart.setTitle("Color repartition")
        self.colorPieChartView = QtCharts.QChartView(self.colorPieChart)
        self.colorPieChartView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.colorPieChartView.setMinimumSize(160, 160)
        self.mainLayout.addWidget(self.colorPieChartView)

    def updateValues(self, updateDict: dict):
        # Mana values graph
        for j, value in enumerate(updateDict["manaValues"]):
            self.manaDataSet.replace(j, value)
        self.deckStatsWidget.setData(updateDict)
        # colorPie
        self.colorPieSeries.clear()
        for color, qty in updateDict["colorPie"].items():
            if color != "":
                _slice = QtCharts.QPieSlice(color, qty)
            else:
                _slice = QtCharts.QPieSlice("colorless", qty)
            _slice.setLabelVisible()
            _color = utils.getColor(color)
            _slice.setColor(QtGui.QColor(_color[0], _color[1], _color[2]))
            self.colorPieSeries.append(_slice)
