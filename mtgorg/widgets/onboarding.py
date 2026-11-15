"""First-launch setup wizard."""

from PySide6 import QtCore, QtGui, QtWidgets

import constants
from lib import qt


def _choiceIcon(kind: str, color: QtGui.QColor, size: int = 54) -> QtGui.QPixmap:
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    painter.setPen(QtGui.QPen(color, 2.8, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap))
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    if kind == "online":
        painter.drawEllipse(8, 8, 38, 38)
        painter.drawLine(8, 27, 46, 27)
        painter.drawArc(13, 8, 28, 38, 90 * 16, 180 * 16)
        painter.setBrush(color)
        for x, y in ((27, 6), (48, 27), (27, 48), (6, 27)):
            painter.drawEllipse(QtCore.QPointF(x, y), 2.3, 2.3)
    else:
        painter.drawEllipse(10, 13, 27, 9)
        painter.drawLine(10, 17, 10, 39)
        painter.drawLine(37, 17, 37, 39)
        painter.drawArc(10, 34, 27, 9, 180 * 16, 180 * 16)
        painter.drawLine(47, 22, 47, 39)
        painter.drawLine(41, 33, 47, 39)
        painter.drawLine(53, 33, 47, 39)
    painter.end()
    return pixmap


class ChoiceCard(QtWidgets.QFrame):
    clicked = QtCore.Signal(str)

    def __init__(self, key: str, title: str, description: str, detail: str, iconKind: str):
        super().__init__()
        self.key = key
        self.setObjectName("choiceCard")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setProperty("selected", False)
        self.setMinimumHeight(190)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        icon = QtWidgets.QLabel()
        icon.setPixmap(_choiceIcon(iconKind, self.palette().color(QtGui.QPalette.ColorRole.Highlight)))
        icon.setFixedSize(54, 54)
        layout.addWidget(icon)
        titleLabel = QtWidgets.QLabel(title)
        titleLabel.setStyleSheet("font-size: 19px; font-weight: 600;")
        layout.addWidget(titleLabel)
        descLabel = QtWidgets.QLabel(description)
        descLabel.setWordWrap(True)
        layout.addWidget(descLabel)
        detailLabel = QtWidgets.QLabel(detail)
        detailLabel.setWordWrap(True)
        detailLabel.setStyleSheet(f"color: {qt.mutedTextColor().name()};")
        layout.addWidget(detailLabel)
        layout.addStretch()
        self.check = QtWidgets.QLabel("✓")
        self.check.setStyleSheet("font-size: 20px; font-weight: bold; color: palette(highlight);")
        self.check.setVisible(False)
        layout.addWidget(self.check, 0, QtCore.Qt.AlignmentFlag.AlignRight)

    def setSelected(self, selected: bool):
        self.setProperty("selected", selected)
        self.check.setVisible(selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)


class DataSourcePage(QtWidgets.QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Choose your card data source")
        self.setSubTitle("Pick one to continue. You can change this later in Settings.")
        self.source = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)
        cards = QtWidgets.QHBoxLayout()
        cards.setSpacing(14)
        self.onlineCard = ChoiceCard(
            "online", "Online", "Fetch card data from Scryfall as you browse.",
            "Always up to date. Needs a connection; a small local cache is used.", "online",
        )
        self.offlineCard = ChoiceCard(
            "offline", "Offline bulk", "Download the card database once and search locally.",
            "About 80 MB download, roughly 0.8–1 GB SQLite index. Works without a connection.", "offline",
        )
        cards.addWidget(self.onlineCard)
        cards.addWidget(self.offlineCard)
        layout.addLayout(cards)

        self.bulkOptions = QtWidgets.QWidget()
        options = QtWidgets.QFormLayout(self.bulkOptions)
        options.setContentsMargins(8, 0, 8, 0)
        self.languageCB = QtWidgets.QComboBox()
        self.languageCB.addItem("English printings (default_cards)", "english")
        self.languageCB.addItem("All languages (all_cards)", "all")
        options.addRow("Bulk language coverage", self.languageCB)
        self.downloadNowCB = QtWidgets.QCheckBox("Download bulk data now")
        self.downloadNowCB.setChecked(True)
        options.addRow("", self.downloadNowCB)
        layout.addWidget(self.bulkOptions)

        note = QtWidgets.QLabel("Your decks and collections are never modified by this setup.")
        note.setStyleSheet(f"color: {qt.mutedTextColor().name()};")
        layout.addWidget(note)
        layout.addStretch()

        self.onlineCard.clicked.connect(self.onChoice)
        self.offlineCard.clicked.connect(self.onChoice)
        self.setBulkEnabled(False)

    def setBulkEnabled(self, enabled: bool):
        self.bulkOptions.setVisible(enabled)

    def onChoice(self, key: str):
        self.source = key
        self.onlineCard.setSelected(key == "online")
        self.offlineCard.setSelected(key == "offline")
        self.setBulkEnabled(key == "offline")
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self.source is not None

    def values(self) -> dict:
        return {
            "use_bulk": self.source == "offline",
            "bulk_language": self.languageCB.currentData(),
            "download_bulk": self.source == "offline" and self.downloadNowCB.isChecked(),
        }


def _previewPixmap(bg: str, base: str, text: str, accent: str) -> QtGui.QPixmap:
    pixmap = QtGui.QPixmap(240, 105)
    pixmap.fill(QtGui.QColor(bg))
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    painter.fillRect(0, 0, 240, 22, QtGui.QColor(base))
    painter.fillRect(0, 22, 50, 83, QtGui.QColor(base).darker(112))
    painter.setPen(QtGui.QColor(text))
    painter.setFont(QtGui.QFont("DejaVu Sans", 8))
    painter.drawText(10, 15, "MTG Organizer")
    for i, y in enumerate((36, 47, 58)):
        painter.fillRect(60, y, 145 - i * 18, 6, QtGui.QColor(text))
    painter.fillRect(60, 72, 58, 20, QtGui.QColor(accent))
    painter.end()
    return pixmap


class ThemeCard(QtWidgets.QFrame):
    clicked = QtCore.Signal(str)

    def __init__(self, key: str, title: str, description: str, preview: QtGui.QPixmap):
        super().__init__()
        self.key = key
        self.setObjectName("themeCard")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setProperty("selected", False)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        previewLabel = QtWidgets.QLabel()
        previewLabel.setPixmap(preview)
        previewLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(previewLabel)
        titleLabel = QtWidgets.QLabel(title)
        titleLabel.setStyleSheet("font-size: 17px; font-weight: 600;")
        layout.addWidget(titleLabel)
        desc = QtWidgets.QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {qt.mutedTextColor().name()};")
        layout.addWidget(desc)
        layout.addStretch()
        self.check = QtWidgets.QLabel("✓")
        self.check.setStyleSheet("font-size: 20px; font-weight: bold; color: palette(highlight);")
        self.check.setVisible(False)
        layout.addWidget(self.check, 0, QtCore.Qt.AlignmentFlag.AlignRight)

    def setSelected(self, selected: bool):
        self.setProperty("selected", selected)
        self.check.setVisible(selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)


class AppearancePage(QtWidgets.QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Appearance")
        self.setSubTitle("Choose how MTG Organizer looks. You can change this later in Settings.")
        self.theme = constants.THEME
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        descriptions = {
            "fusion": "Follows system light/dark.",
            "kde": "Native KDE colors; Breeze widgets when available.",
            "material": "Follows system light/dark; teal accents.",
        }
        dark = qt.systemPrefersDark()
        if dark:
            systemBg, systemBase, systemText, systemAccent = "#202326", "#232629", "#fcfcfc", "#3daee9"
            materialBg, materialBase, materialText, materialAccent = "#232629", "#31363b", "#ffffff", "#1de9b6"
        else:
            systemBg, systemBase, systemText, systemAccent = "#eff0f1", "#ffffff", "#232629", "#3daee9"
            materialBg, materialBase, materialText, materialAccent = "#f5f5f5", "#ffffff", "#3c3c3c", "#1de9b6"
        previews = {
            "fusion": _previewPixmap(systemBg, systemBase, systemText, systemAccent),
            "kde": _previewPixmap(systemBg, systemBase, systemText, systemAccent),
            "material": _previewPixmap(materialBg, materialBase, materialText, materialAccent),
        }
        self.cards = []
        cardsLayout = QtWidgets.QHBoxLayout()
        cardsLayout.setSpacing(12)
        for key, label in constants.availableThemes().items():
            card = ThemeCard(key, label, descriptions.get(key, ""), previews[key])
            card.clicked.connect(self.onChoice)
            cardsLayout.addWidget(card)
            self.cards.append(card)
        layout.addLayout(cardsLayout)
        note = QtWidgets.QLabel("Changes apply when setup finishes.")
        note.setStyleSheet(f"color: {qt.mutedTextColor().name()};")
        layout.addWidget(note)
        layout.addStretch()
        self.select(self.theme)

    def select(self, key: str):
        if key not in constants.availableThemes():
            key = "fusion"
        self.theme = key
        for card in self.cards:
            card.setSelected(card.key == key)

    def onChoice(self, key: str):
        self.select(key)


class UpdatesPage(QtWidgets.QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Updates")
        self.setSubTitle("Stay informed about new MTG Organizer releases.")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        self.autoCheckCB = QtWidgets.QCheckBox("Check for new releases automatically")
        self.autoCheckCB.setChecked(True)
        self.autoCheckCB.setStyleSheet("font-size: 17px; font-weight: 600;")
        layout.addWidget(self.autoCheckCB)
        body = QtWidgets.QLabel(
            "MTG Organizer checks GitHub Releases once per day and shows a notification "
            "when a newer version is available. No account or personal data is needed."
        )
        body.setWordWrap(True)
        layout.addWidget(body)
        note = QtWidgets.QLabel("You can also check manually from Settings.")
        note.setStyleSheet(f"color: {qt.mutedTextColor().name()};")
        layout.addWidget(note)
        layout.addStretch()


class OnboardingWizard(QtWidgets.QWizard):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Setup - MTG Organizer")
        self.setWizardStyle(QtWidgets.QWizard.WizardStyle.ModernStyle)
        self.setWindowIcon(QtGui.QIcon(constants.resourcePath("icons", "mirari.png").as_posix()))
        self.setButtonText(QtWidgets.QWizard.WizardButton.NextButton, "Continue")
        self.setOption(QtWidgets.QWizard.WizardOption.NoBackButtonOnStartPage)
        self.resize(820, 560)
        self.setStyleSheet("""
            #choiceCard, #themeCard {
                background-color: palette(base);
                border: 2px solid palette(mid);
                border-radius: 10px;
            }
            #choiceCard:hover, #themeCard:hover { border-color: palette(highlight); }
            #choiceCard[selected="true"], #themeCard[selected="true"] {
                background-color: palette(alternate-base);
                border: 3px solid palette(highlight);
            }
        """)
        self.dataPage = DataSourcePage()
        self.appearancePage = AppearancePage()
        self.updatesPage = UpdatesPage()
        self.addPage(self.dataPage)
        self.addPage(self.appearancePage)
        self.addPage(self.updatesPage)

        finish = QtWidgets.QWizardPage()
        finish.setTitle("Ready")
        finish.setSubTitle("MTG Organizer is ready to use.")
        finishLayout = QtWidgets.QVBoxLayout(finish)
        finishLayout.addWidget(QtWidgets.QLabel("You can change these options later in Settings."))
        finishLayout.addStretch()
        self.addPage(finish)

    def values(self) -> dict:
        values = self.dataPage.values()
        values.update({
            "theme": self.appearancePage.theme,
            "check_updates": self.updatesPage.autoCheckCB.isChecked(),
        })
        return values
