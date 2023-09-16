from PySide6 import QtWidgets, QtCore, QtCharts, QtGui

from widgets.cardlistwidget import CardStackListWidget
from lib import utils, qt

import constants

GRAPH_MIN_SIZE = (240, 240)


class CardsList(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # Display currently selected deck/collection
    def __init__(self, parent=None, **kwargs):
        super(CardsList, self).__init__(parent=parent, **kwargs)
        self.sortBy = None
        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        self.mainLayout.addWidget(self.splitter)

        # Left (main pane) is cards list
        self.cardsListWidget = QtWidgets.QWidget()
        self.cardsListLayout = QtWidgets.QVBoxLayout()
        self.cardsListWidget.setLayout(self.cardsListLayout)
        self.cardsListButtonBox = QtWidgets.QWidget()
        self.cardsListButtonBoxLayout = QtWidgets.QHBoxLayout()
        self.cardsListButtonBox.setLayout(self.cardsListButtonBoxLayout)
        self.cardsListButtonBoxLayout.addWidget(QtWidgets.QLabel("Sort by:"))
        self.cardsListButton_type = QtWidgets.QPushButton("Type")
        self.cardsListButton_type.clicked.connect(self.on_sortByType)
        self.cardsListButtonBoxLayout.addWidget(self.cardsListButton_type)
        self.cardsListButton_price = QtWidgets.QPushButton("Price")
        self.cardsListButton_price.clicked.connect(self.on_sortByPrice)
        self.cardsListButtonBoxLayout.addWidget(self.cardsListButton_price)
        self.cardsListButton_name = QtWidgets.QPushButton("Name")
        self.cardsListButton_name.clicked.connect(self.on_sortByName)
        self.cardsListButtonBoxLayout.addWidget(self.cardsListButton_name)
        self.cardsListButton_cmc = QtWidgets.QPushButton("CMC")
        self.cardsListButton_cmc.clicked.connect(self.on_sortByCmc)
        self.cardsListButtonBoxLayout.addWidget(self.cardsListButton_cmc)
        self.cardsListLayout.addWidget(self.cardsListButtonBox)
        self.cardsList = CardStackListWidget(parent=self)
        self.cardsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.cardsList.itemChanged.connect(self.cardsList.on_itemChanged)
        self.cardsListLayout.addWidget(self.cardsList)
        self.splitter.addWidget(self.cardsListWidget)

        # Right pane is infos data (text, graphs, list, ...)
        self.infoPanel = InfoWidget()
        self.qscroll = QtWidgets.QScrollArea()
        self.qscroll.setWidgetResizable(True)
        self.qscroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.qscroll.setWidget(self.infoPanel)
        self.splitter.addWidget(self.qscroll)

    def on_dbSelectChanged(self):
        if len(self.cardsList.selectedItems()) == 1:
            selectedItem = self.cardsList.selectedItems()[0]
            self.cardSelected.emit(selectedItem.data(QtCore.Qt.UserRole)["data"]["id"])
        else:
            selectedItem = None

    def sort(self, key: str = None):
        if key is None:
            key = self.sortBy
        else:
            self.sortBy = key
        if key == "prices":
            cardsList = self.cardsList.cardStack
            cardsList.sort(
                key=lambda x: float(
                    utils.getFromDict(
                        x[1], [key, constants.CURRENCY[0]], 0
                    ) if utils.getFromDict(
                        x[1], [key, constants.CURRENCY[0]], 0
                    ) is not None else 0
                )
            )
        else:
            cardsList = self.cardsList.cardStack
            cardsList.sort(key=lambda x: x[1][key])
        self.cardsList.setCards(cardsList)

    def on_sortByType(self):
        self.sort("type_line")

    def on_sortByPrice(self):
        self.sort("prices")

    def on_sortByName(self):
        self.sort("name")

    def on_sortByCmc(self):
        self.sort("cmc")


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

        self._totalCmcLabel = QtWidgets.QLabel("Total CMC")
        self.mainLayout.addWidget(self._totalCmcLabel, 2, 0)
        self.totalCmcLabel = QtWidgets.QLabel()
        self.mainLayout.addWidget(self.totalCmcLabel, 2, 1)

    def setData(self, dataDict):
        self.cardCountLabel.setText(
            str(dataDict["cardCount"])
        )
        self.totalPriceLabel.setText(
            str(round(dataDict["totalPrice"], 2)) + constants.CURRENCY[1]
        )
        self.totalCmcLabel.setText(
            str(round(dataDict["totalCmc"], 2))
        )


class InfoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Deck stats
        self.deckStatsWidget = DeckStatsWidget()
        self.mainLayout.addWidget(self.deckStatsWidget)

        # Legalities
        self.legalitiesWidget = LegalitiesWidget(self)
        self.mainLayout.addWidget(self.legalitiesWidget)

        # Mana cost
        # Data series
        self.manaBarSeries = QtCharts.QBarSeries()
        self.manaDataSet = QtCharts.QBarSet("Mana Cost")
        self.manaDataSet.append([0, 0, 0, 0, 0, 0, 0])
        self.manaBarSeries.append(self.manaDataSet)
        self.manaBarSeries.append(self.manaDataSet)
        self.manaChart = QtCharts.QChart()
        self.manaChart.setTitle("Mana repartition")
        self.manaChart.addSeries(self.manaBarSeries)
        self.manaChart.setTheme(qt.getChartsTheme())
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
        self.manaChartView.setMinimumSize(GRAPH_MIN_SIZE[0], GRAPH_MIN_SIZE[1])
        self.mainLayout.addWidget(self.manaChartView)

        # Color repartition
        self.colorPieChart = QtCharts.QChart()
        self.colorPieChart.setTheme(qt.getChartsTheme())
        self.colorPieChart.createDefaultAxes()
        self.colorPieSeries = QtCharts.QPieSeries()
        self.colorPieChart.addSeries(self.colorPieSeries)
        self.colorPieChart.legend().setVisible(False)
        self.colorPieChart.setTitle("Color repartition")
        self.colorPieChartView = QtCharts.QChartView(self.colorPieChart)
        self.colorPieChartView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.colorPieChartView.setMinimumSize(GRAPH_MIN_SIZE[0], GRAPH_MIN_SIZE[1] * 1.2)
        self.colorPieChartView.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.mainLayout.addWidget(self.colorPieChartView)

        # Card type repartition
        self.typePieChart = QtCharts.QChart()
        self.typePieChart.setTheme(qt.getChartsTheme())
        self.typePieChart.createDefaultAxes()
        self.typePieSeries = QtCharts.QPieSeries()
        self.typePieChart.addSeries(self.typePieSeries)
        self.typePieChart.legend().setVisible(False)
        self.typePieChart.setTitle("Type repartition")
        self.typePieChartView = QtCharts.QChartView(self.typePieChart)
        self.typePieChartView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.typePieChartView.setMinimumSize(GRAPH_MIN_SIZE[0], GRAPH_MIN_SIZE[1] * 1.2)
        self.mainLayout.addWidget(self.typePieChartView)

    def updateValues(self, updateDict: dict):
        # Main data
        self.deckStatsWidget.setData(updateDict)
        # Legalities
        self.legalitiesWidget.displayLegalities(updateDict["legalities"])
        # Mana values graph
        for j, value in enumerate(updateDict["manaValues"]):
            self.manaDataSet.replace(j, value)
        self.manaAxisY.setMax(max(updateDict["manaValues"]))
        # colorPie
        self.colorPieSeries.clear()
        for color, qty in updateDict["colorPie"].items():
            if color != "":
                _slice = QtCharts.QPieSlice(f"{color}: {qty}", qty)
            else:
                _slice = QtCharts.QPieSlice(f"colorless: {qty}", qty)
            _slice.setLabelVisible()
            _color = utils.getColor(color)
            _slice.setColor(QtGui.QColor(_color[0], _color[1], _color[2]))
            self.colorPieSeries.append(_slice)
        # typePie
        self.typePieSeries.clear()
        for type, qty in updateDict["typePie"].items():
            _slice = QtCharts.QPieSlice(f"{type}: {qty}", qty)
            _slice.setLabelVisible()
            self.typePieSeries.append(_slice)


class LegalitiesWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None) -> None:
        super().__init__(parent)
        self.mainLayout = qt.FlowLayout()
        self.setLayout(self.mainLayout)
        self.legalitiesWidgets = {}

    def clear(self):
        # Remove all checkboxes
        for _widget in self.legalitiesWidgets.values():
            _widget.deleteLater()
        self.legalitiesWidgets = {}

    def displayLegalities(self, legalitiesDict):
        self.clear()
        for k, v in legalitiesDict.items():
            _legalityCB = QtWidgets.QCheckBox(k)
            _legalityCB.setEnabled(False)
            _legalityCB.setChecked(v == "legal")
            _legalityCB.setMaximumHeight(24)
            # TODO add tooltip to say what is not legal
            self.mainLayout.addWidget(_legalityCB)
            self.legalitiesWidgets.update({k: _legalityCB})
