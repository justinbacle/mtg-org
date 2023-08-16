from PySide6 import QtWidgets, QtCore, QtCharts, QtGui

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
        self.setMaximumWidth(320)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        # Mana cost
        # Data series
        self.barSeries = QtCharts.QBarSeries()
        self.dataSet = QtCharts.QBarSet("Mana Cost")
        self.dataSet.append([1, 2, 3, 4, 5, 6, 7])
        self.barSeries.append(self.dataSet)
        self.barSeries.append(self.dataSet)
        self.chart = QtCharts.QChart()
        self.chart.setTitle("Mana repartition")
        self.chart.addSeries(self.barSeries)
        # Axes
        self.categories = ["0", "1", "2", "3", "4", "5", "6+"]
        self.axisX = QtCharts.QBarCategoryAxis()
        self.axisX.append(self.categories)
        self.barSeries.attachAxis(self.axisX)
        self.axisY = QtCharts.QValueAxis()
        self.chart.addAxis(self.axisX, QtCore.Qt.AlignBottom)
        self.chart.addAxis(self.axisY, QtCore.Qt.AlignLeft)
        self.barSeries.attachAxis(self.axisY)
        # legend
        self.chart.legend().setVisible(False)
        self.chart.legend().setAlignment(QtCore.Qt.AlignBottom)
        # View
        self.chartView = QtCharts.QChartView(self.chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.chartView.setMinimumSize(160, 160)
        self.mainLayout.addWidget(self.chartView)

    def updateValues(self, updateDict: dict):
        # Mana values graph
        for j, value in enumerate(updateDict["manaValues"]):
            self.dataSet.replace(j, value)
