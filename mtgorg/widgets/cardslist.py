from PySide6 import QtWidgets, QtCore, QtCharts, QtGui

import html
import re

from widgets.cardlistwidget import CardStackListWidget
from lib import advisor, scryfall, utils, qt

import connector
import constants
from lib import deckrules

GRAPH_MIN_SIZE = (240, 240)


class CardsList(QtWidgets.QWidget):
    cardSelected: QtCore.Signal = QtCore.Signal(str)

    # Display currently selected deck/collection
    def __init__(self, parent=None, **kwargs):
        super(CardsList, self).__init__(parent=parent, **kwargs)
        self.sortBy = None
        self.stackType = None
        self.stackName = None
        self.initUi()

    def initUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        qt.configureSplitter(self.splitter)
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
        self.cardsListButton_color = QtWidgets.QPushButton("Color")
        self.cardsListButton_color.clicked.connect(self.on_sortByColor)
        self.cardsListButtonBoxLayout.addWidget(self.cardsListButton_color)
        self.cardsListButtonBoxLayout.addStretch()

        self.cardsListLayout.addWidget(self.cardsListButtonBox)

        self.deckLoadingLabel = QtWidgets.QLabel("Loading deck...")
        self.deckLoadingLabel.setStyleSheet(f"color: {qt.mutedTextColor().name()};")
        self.deckLoadingLabel.setVisible(False)
        self.cardsListLayout.addWidget(self.deckLoadingLabel)

        self.deckLoadingBar = QtWidgets.QProgressBar()
        self.deckLoadingBar.setRange(0, 1)
        self.deckLoadingBar.setValue(0)
        self.deckLoadingBar.setMaximumHeight(6)
        self.deckLoadingBar.setTextVisible(False)
        self.deckLoadingBar.setVisible(False)
        self.cardsListLayout.addWidget(self.deckLoadingBar)
        self._deckLoadingTimer = QtCore.QTimer(self)
        self._deckLoadingTimer.setInterval(70)
        self._deckLoadingTimer.timeout.connect(self._tickDeckLoading)

        self.cardsList = CardStackListWidget(parent=self)
        self.cardsList.itemSelectionChanged.connect(self.on_dbSelectChanged)
        self.cardsList.itemChanged.connect(self.cardsList.on_itemChanged)
        self.cardsList.cardListChanged.connect(self.refreshValidation)
        self.cardsList.sectionsLoaded.connect(self.onCardsLoaded)
        self.cardsListLayout.addWidget(self.cardsList, 1)
        self.splitter.addWidget(self.cardsListWidget)

        # Right pane is infos data (text, graphs, list, ...)
        self.infoPanel = InfoWidget()
        self.qscroll = QtWidgets.QScrollArea()
        self.qscroll.setWidgetResizable(True)
        self.qscroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.qscroll.setWidget(self.infoPanel)
        self.splitter.addWidget(self.qscroll)
        self.splitter.setSizes([900, 420])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

    def applyTheme(self):
        self.infoPanel.applyTheme()

    def setCardStack(self, cardStack, stackType: str | None, stackName: str | None):
        self.stackType = stackType
        self.stackName = stackName
        if stackType == "deck":
            formatKey = cardStack.get("format", constants.DEFAULT_DECK_FORMAT)
            allowed = deckrules.allowedSections(formatKey)
            sections = {
                "main": cardStack.get("cardList", []),
                "sideboard": cardStack.get("sideboard", []),
                "commander": cardStack.get("commander", []),
                "companion": cardStack.get("companion", []),
            }
        else:
            allowed = {"main"}
            sections = {"main": cardStack["cardList"]}
        showSectionHeaders = stackType == "deck"
        self.deckLoadingLabel.setVisible(True)
        self.deckLoadingBar.setRange(0, 100)
        self.deckLoadingBar.setValue(0)
        self.deckLoadingBar.setVisible(True)
        self._deckLoadingTimer.start()
        QtWidgets.QApplication.processEvents()
        self.cardsList.setSections(sections, allowed, showSectionHeaders=showSectionHeaders)

    def _tickDeckLoading(self):
        self.deckLoadingBar.setValue((self.deckLoadingBar.value() + 7) % 100)

    def _stopDeckLoading(self):
        self._deckLoadingTimer.stop()
        self.deckLoadingLabel.setVisible(False)
        self.deckLoadingBar.setVisible(False)

    def onCardsLoaded(self):
        try:
            self.refreshValidation()
        finally:
            self._stopDeckLoading()

    def _loadedCardLookup(self, cardId: str):
        for entries in self.cardsList.sectionCardStacks.values():
            for _qty, card in entries:
                if card.get("id") == cardId:
                    return card
        return scryfall.getCardById(cardId)

    def refreshValidation(self):
        if self.stackType == "deck" and self.stackName is not None:
            deck = connector.getDeck(self.stackName)
            if deck is not None:
                self.infoPanel.setValidationDetails(deckrules.validateDeckDetails(deck, self._loadedCardLookup))
                self.infoPanel.setAdvisorFindings(advisor.analyzeCommander(deck, self._loadedCardLookup))
                self.infoPanel.setAdvisorCurveTarget(advisor.commanderCurveTarget(deck, self._loadedCardLookup))
                return
        self.infoPanel.setValidationDetails(None)
        self.infoPanel.setAdvisorFindings([])
        self.infoPanel.setAdvisorCurveTarget(None)

    def replaceCardInAnySection(self, oldCardId: str, newCardId: str):
        if self.stackName is None:
            return
        if self.stackType == "collection":
            connector.replaceCardInCollection(self.stackName, oldCardId, newCardId)
            self.cardsList.reloadFromDatabase()
            self.refreshValidation()
            return
        if self.stackType != "deck":
            return
        deck = connector.getDeck(self.stackName)
        if deck is None:
            return
        for section, key in connector.DECK_SECTION_KEYS.items():
            if any(entry[1] == oldCardId for entry in deck.get(key, [])):
                connector.replaceCardInDeck(self.stackName, oldCardId, newCardId, section=section)
                self.cardsList.reloadFromDatabase()
                self.refreshValidation()
                return

    def on_dbSelectChanged(self):
        if len(self.cardsList.selectedItems()) == 1:
            selectedItem = self.cardsList.selectedItems()[0]
            data = selectedItem.data(QtCore.Qt.ItemDataRole.UserRole)
            if data is not None:
                self.cardSelected.emit(data["data"]["id"])

    def on_dbSelectChangedFor(self, table):
        if len(table.selectedItems()) == 1:
            selectedItem = table.selectedItems()[0]
            self.cardSelected.emit(selectedItem.data(QtCore.Qt.ItemDataRole.UserRole)["data"]["id"])

    def sort(self, key: str | None = None):
        if key is None:
            key = self.sortBy
        else:
            self.sortBy = key
        self.cardsList.sortSections(key)

    def on_sortByType(self):
        self.sort("type_line")

    def on_sortByPrice(self):
        self.sort("prices")

    def on_sortByName(self):
        self.sort("name")

    def on_sortByCmc(self):
        self.sort("cmc")

    def on_sortByColor(self):
        self.sort("colors")


class DeckStatsWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
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


class DynamicTabWidget(QtWidgets.QTabWidget):
    """Size the tab widget to its current page, not the tallest page."""

    def sizeHint(self):
        current = self.currentWidget()
        return current.sizeHint() if current is not None else super().sizeHint()

    def minimumSizeHint(self):
        current = self.currentWidget()
        return current.minimumSizeHint() if current is not None else super().minimumSizeHint()


class InfoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Deck stats
        self.deckStatsWidget = DeckStatsWidget()
        self.mainLayout.addWidget(self.deckStatsWidget)

        self.tabs = DynamicTabWidget()
        self.tabs.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        self.mainLayout.addWidget(self.tabs)
        self.mainLayout.addStretch(1)
        self.statsTab = QtWidgets.QWidget()
        self.statsLayout = QtWidgets.QVBoxLayout(self.statsTab)
        self.statsLayout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.statsTab, "Stats")

        # Mana cost
        # Data series
        self.manaBarSeries = QtCharts.QBarSeries()
        self.manaDataSet = QtCharts.QBarSet("Deck")
        self.manaDataSet.append([0, 0, 0, 0, 0, 0, 0])
        self.recommendedDataSet = QtCharts.QBarSet("Recommended")
        self.recommendedDataSet.append([0, 0, 0, 0, 0, 0, 0])
        self.recommendedDataSet.setColor(QtGui.QColor(130, 136, 145, 180))
        self.manaBarSeries.append(self.manaDataSet)
        self.manaBarSeries.append(self.recommendedDataSet)
        self._recommendedValues = [0] * 7
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
        self.manaChart.addAxis(self.manaAxisX, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.manaChart.addAxis(self.manaAxisY, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.manaBarSeries.attachAxis(self.manaAxisY)
        # legend
        self.manaChart.legend().setVisible(False)
        self.manaChart.legend().setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom)
        # View
        self.manaChartView = QtCharts.QChartView(self.manaChart)
        self.manaChartView.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.manaChartView.setMinimumSize(GRAPH_MIN_SIZE[0], GRAPH_MIN_SIZE[1])
        self.statsLayout.addWidget(self.manaChartView)

        # Color repartition
        self.colorPieChart = QtCharts.QChart()
        self.colorPieChart.setTheme(qt.getChartsTheme())
        self.colorPieChart.createDefaultAxes()
        self.colorPieSeries = QtCharts.QPieSeries()
        self.colorPieChart.addSeries(self.colorPieSeries)
        self.colorPieChart.legend().setVisible(False)
        self.colorPieChart.setTitle("Color repartition")
        self.colorPieChartView = QtCharts.QChartView(self.colorPieChart)
        self.colorPieChartView.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.colorPieChartView.setMinimumSize(GRAPH_MIN_SIZE[0], int(GRAPH_MIN_SIZE[1] * 1.2))
        self.colorPieChartView.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.statsLayout.addWidget(self.colorPieChartView)

        # Card type repartition
        self.typePieChart = QtCharts.QChart()
        self.typePieChart.setTheme(qt.getChartsTheme())
        self.typePieChart.createDefaultAxes()
        self.typePieSeries = QtCharts.QPieSeries()
        self.typePieChart.addSeries(self.typePieSeries)
        self.typePieChart.legend().setVisible(False)
        self.typePieChart.setTitle("Type repartition")
        self.typePieChartView = QtCharts.QChartView(self.typePieChart)
        self.typePieChartView.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.typePieChartView.setMinimumSize(GRAPH_MIN_SIZE[0], int(GRAPH_MIN_SIZE[1] * 1.2))
        self.statsLayout.addWidget(self.typePieChartView)

        self.advisorWidget = AdvisorWidget()
        self.advisorTabIndex = self.tabs.addTab(self.advisorWidget, "Advisor")
        self.tabs.setTabVisible(self.advisorTabIndex, False)

        self.formatLegalityWidget = FormatLegalityWidget(self)
        self.legalityTabIndex = self.tabs.addTab(self.formatLegalityWidget, "Legality")
        self._lastValues = None
        self.tabs.currentChanged.connect(self._onTabChanged)
        self.applyTheme()

    def _onTabChanged(self, _index: int):
        QtCore.QTimer.singleShot(0, self._fitTabHeight)

    def _fitTabHeight(self):
        current = self.tabs.currentWidget()
        if current is None:
            return
        height = current.sizeHint().height()
        layout = current.layout()
        if layout is not None:
            height = max(height, layout.sizeHint().height())
        self.tabs.setFixedHeight(max(height, 120))
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fitTabHeight()

    def applyTheme(self):
        for chart in (self.manaChart, self.colorPieChart, self.typePieChart):
            qt.styleChart(chart)
        for view in (self.manaChartView, self.colorPieChartView, self.typePieChartView):
            qt.styleChartView(view)
        if self._lastValues is not None:
            self.updateValues(self._lastValues)

    def setValidationDetails(self, details: dict | None):
        self.formatLegalityWidget.setDetails(details)
        self.tabs.setTabVisible(self.legalityTabIndex, details is not None)
        if details is None and self.tabs.currentIndex() == self.legalityTabIndex:
            self.tabs.setCurrentIndex(0)

    def setAdvisorFindings(self, findings: list[dict]):
        self.advisorWidget.setFindings(findings)
        self.tabs.setTabText(self.advisorTabIndex, f"Advisor ({len(findings)})")
        self.tabs.setTabVisible(self.advisorTabIndex, bool(findings))
        if not findings and self.tabs.currentIndex() == self.advisorTabIndex:
            self.tabs.setCurrentIndex(0)

    def setAdvisorCurveTarget(self, target: list[int] | None):
        if target:
            values = [0, *target[:5], target[5]]
            self.manaChart.legend().setVisible(True)
            self.manaChart.legend().setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom)
        else:
            values = [0] * 7
            self.manaChart.legend().setVisible(False)
        self._recommendedValues = values
        for index, value in enumerate(values):
            self.recommendedDataSet.replace(index, value)
        if self._lastValues is not None:
            self.manaAxisY.setMax(max(self._lastValues["manaValues"] + values))

    def updateValues(self, updateDict: dict):
        self._lastValues = updateDict
        labelColor = qt.chartTextColor()
        # Main data
        self.deckStatsWidget.setData(updateDict)
        # Mana values graph
        for j, value in enumerate(updateDict["manaValues"]):
            self.manaDataSet.replace(j, value)
        self.manaAxisY.setMax(max(updateDict["manaValues"] + self._recommendedValues))
        # colorPie
        self.colorPieSeries.clear()
        for color, qty in updateDict["colorPie"].items():
            if color != "":
                _slice = QtCharts.QPieSlice(f"{color}: {qty}", qty)
            else:
                _slice = QtCharts.QPieSlice(f"colorless: {qty}", qty)
            _slice.setLabelVisible()
            _slice.setLabelColor(labelColor)
            _color = utils.getColor(color)
            _slice.setColor(QtGui.QColor(_color[0], _color[1], _color[2]))
            self.colorPieSeries.append(_slice)
        # typePie
        self.typePieSeries.clear()
        for type, qty in updateDict["typePie"].items():
            _slice = QtCharts.QPieSlice(f"{type}: {qty}", qty)
            _slice.setLabelVisible()
            _slice.setLabelColor(labelColor)
            self.typePieSeries.append(_slice)


class AdvisorWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(8, 8, 8, 8)
        self.mainLayout.setSpacing(6)
        self.findingsLayout = QtWidgets.QVBoxLayout()
        self.findingsLayout.setSpacing(4)
        self.mainLayout.addLayout(self.findingsLayout)
        self.mainLayout.addStretch()

    def clear(self):
        while self.findingsLayout.count():
            item = self.findingsLayout.takeAt(0)
            if item.widget() is not None:
                widget = item.widget()
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _renderManaText(self, text: str) -> str:
        parts = re.split(r"(\{[^}]+\}(?:\s*\{[^}]+\})*)", text)
        rendered = []
        for part in parts:
            if part.startswith("{"):
                rendered.append(
                    f"<span style=\"font-family: 'Proxyglyph'; font-size: 14pt;\">"
                    f"{html.escape(utils.setManaText(part))}</span>"
                )
            elif part:
                rendered.append(html.escape(part))
        return "".join(rendered)

    def _formatFinding(self, finding: dict) -> str:
        labels = {"warning": "Warning", "tip": "Tip", "info": "Info"}
        text = f"<b>{labels.get(finding['severity'], 'Info')}:</b> {self._renderManaText(finding['text'])}"
        for detail in finding.get("details", []):
            text += f"<br>&nbsp;&nbsp;{self._renderManaText(detail)}"
        coverage = finding.get("coverage", [])
        if coverage:
            text += "<br><table cellspacing='0' cellpadding='2'>"
            for row in coverage:
                text += (
                    "<tr>"
                    f"<td><b>{html.escape(row['category'])}</b></td>"
                    f"<td align='right'>&nbsp;{row['count']}</td>"
                    f"<td>&nbsp;&nbsp;{html.escape(row['cards'])}</td>"
                    "</tr>"
                )
            text += "</table>"
        text += f"<br><a href=\"{finding['source']}\">({finding['sourceLabel']})</a>"
        return text

    def setFindings(self, findings: list[dict]):
        self.clear()
        if not findings:
            return
        for finding in findings:
            card = QtWidgets.QFrame()
            card.setObjectName("advisorCard")
            card.setStyleSheet(
                "#advisorCard { background-color: palette(base); "
                "border: 1px solid palette(mid); border-radius: 6px; }"
            )
            cardLayout = QtWidgets.QVBoxLayout(card)
            cardLayout.setContentsMargins(10, 8, 10, 8)
            label = QtWidgets.QLabel(self._formatFinding(finding))
            label.setWordWrap(True)
            label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            label.setOpenExternalLinks(True)
            cardLayout.addWidget(label)
            self.findingsLayout.addWidget(card)


class FormatLegalityWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(6)

        header = QtWidgets.QHBoxLayout()
        self.titleLabel = QtWidgets.QLabel("Format legality")
        self.titleLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self.titleLabel)
        header.addStretch()
        self.statusButton = QtWidgets.QToolButton()
        self.statusButton.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.statusButton.setAutoRaise(True)
        header.addWidget(self.statusButton)
        self.mainLayout.addLayout(header)

        self.bracketLabel = QtWidgets.QLabel("")
        self.bracketLabel.setWordWrap(True)
        self.bracketLabel.setVisible(False)
        self.mainLayout.addWidget(self.bracketLabel)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Card", "Status", "Reason"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 115)
        self.table.setColumnWidth(1, 74)
        self.table.setMinimumHeight(180)
        self.mainLayout.addWidget(self.table)
        self.setVisible(False)

    def _setStatus(self, text: str, ok: bool):
        icon = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton if ok else (
            QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning
        )
        self.statusButton.setIcon(self.style().standardIcon(icon))
        self.statusButton.setText(text)
        self.statusButton.setToolTip("No issues" if ok else text)

    def _addRow(self, card: str, status: str, reason: str, ok: bool):
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = (card, status, reason)
        for col, value in enumerate(values):
            item = QtWidgets.QTableWidgetItem(value)
            item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)
            if col == 1:
                item.setForeground(QtGui.QColor("#6fcf97" if ok else "#eb5757"))
            if col == 2:
                item.setToolTip(value)
            self.table.setItem(row, col, item)

    def setDetails(self, details: dict | None):
        self.table.setRowCount(0)
        if details is None:
            self.bracketLabel.setVisible(False)
            return
        bracket = details.get("bracket")
        if bracket is None:
            self.bracketLabel.setVisible(False)
        else:
            selected = bracket.get("selected")
            floor = bracket.get("floor", 1)
            if selected is None:
                bracketText = f"Commander bracket: not set — suggested minimum Bracket {floor}"
                color = "#b8bcc2"
            else:
                bracketText = f"Commander bracket: {selected} — suggested minimum Bracket {floor}"
                color = "#e0a040" if selected < floor else "#b8bcc2"
            counts = (
                f"Game Changers: {len(bracket.get('gameChangers', []))} · "
                f"Extra turns: {len(bracket.get('extraTurns', []))} · "
                f"Mass land denial: {len(bracket.get('massLandDenial', []))} · "
                f"Tutors: {len(bracket.get('tutors', []))} · "
                f"Possible combos: {len(bracket.get('possibleCombos', []))}"
            )
            self.bracketLabel.setText(f"{bracketText}\n{counts}")
            self.bracketLabel.setStyleSheet(f"color:{color};")
            self.bracketLabel.setToolTip("\n".join(bracket.get("guidance", [])))
            self.bracketLabel.setVisible(True)
        issues = details.get("issues", [])
        cards = details.get("cards", [])
        total = len(issues) + len(cards)
        self.titleLabel.setText(f"{details.get('label', 'Format')} legality")
        self._setStatus("Legal" if total == 0 else f"{total} issue(s)", total == 0)
        if total == 0:
            self._addRow("Deck", "✓", "No issues", True)
        else:
            for message in issues:
                self._addRow("Deck", "✗", message, False)
            for issue in cards:
                self._addRow(issue["card"], issue["status"], issue["reason"], False)
        self.table.resizeRowsToContents()
