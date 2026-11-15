import logging
from types import SimpleNamespace

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QTest

import widgets.dbbrowser as dbbrowser
from lib import qt


class DummyCardList:
    def __init__(self):
        self.cards = None

    def setCards(self, cards):
        self.cards = cards


class DummyLabel:
    def __init__(self):
        self.text = ""
        self.visible = False

    def setText(self, text):
        self.text = text

    def setVisible(self, visible):
        self.visible = visible

    def clear(self):
        self.text = ""


def test_search_request_is_logged(caplog):
    with caplog.at_level(logging.INFO):
        dbbrowser.DbBrowser._logSearchRequest({"loy": ">5", "types": ["planeswalker"]})

    assert "Search request" in caplog.text
    assert "planeswalker" in caplog.text


def test_no_results_search_is_logged(monkeypatch, caplog):
    browser = SimpleNamespace(dbResultsList=DummyCardList(), resultsInfoLabel=DummyLabel())

    with caplog.at_level(logging.INFO):
        dbbrowser.DbBrowser._applySearchResults(browser, [], "zzzzzzzz")

    assert "No cards found for search" in caplog.text
    assert browser.dbResultsList.cards == []
    assert browser.resultsInfoLabel.visible is False


def test_truncated_search_shows_indicator(caplog):
    browser = SimpleNamespace(dbResultsList=DummyCardList(), resultsInfoLabel=DummyLabel())

    with caplog.at_level(logging.INFO):
        dbbrowser.DbBrowser._applySearchResults(browser, [{"id": "1"}], "lightning", True)

    assert "more cards match" in caplog.text
    assert browser.resultsInfoLabel.visible is True
    assert "Refine your search" in browser.resultsInfoLabel.text
    assert browser.dbResultsList.cards == [(1, {"id": "1"})]


def test_search_worker_emits_results(monkeypatch):
    monkeypatch.setattr(
        dbbrowser.scryfall,
        "searchCardsLimited",
        lambda searchDict, limit: ([{"id": "card-1"}], False),
    )
    worker = dbbrowser.SearchWorker(3, {"name": "x"}, 100)
    results = []
    worker.finished.connect(
        lambda requestId, cards, truncated: results.append((requestId, cards, truncated))
    )

    worker.run()

    assert results == [(3, [{"id": "card-1"}], False)]


def test_search_worker_emits_failure(monkeypatch):
    def fail(searchDict, limit):
        raise RuntimeError("boom")

    monkeypatch.setattr(dbbrowser.scryfall, "searchCardsLimited", fail)
    worker = dbbrowser.SearchWorker(4, {"name": "x"}, 100)
    failures = []
    worker.failed.connect(lambda requestId, error: failures.append((requestId, error)))

    worker.run()

    assert failures[0][0] == 4
    assert "RuntimeError" in failures[0][1]


def test_no_wheel_combo_ignores_scroll(qtApp):
    combo = qt.NoWheelComboBox()
    combo.addItems(["a", "b"])
    combo.setCurrentIndex(0)
    event = QtGui.QWheelEvent(
        QtCore.QPointF(1, 1),
        QtCore.QPointF(1, 1),
        QtCore.QPoint(0, 0),
        QtCore.QPoint(0, 120),
        QtCore.Qt.MouseButton.NoButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
        QtCore.Qt.ScrollPhase.NoScrollPhase,
        False,
    )

    combo.wheelEvent(event)

    assert combo.currentIndex() == 0


def test_enter_triggers_search_from_all_text_fields(qtApp, monkeypatch):
    monkeypatch.setattr(
        dbbrowser.scryfall,
        "getSets",
        lambda: [{"id": "set-1", "code": "tst", "name": "Test Set", "released_at": "2024-01-01"}],
    )
    monkeypatch.setattr(dbbrowser.scryfall, "getSetReleaseYear", lambda setId: "2024")
    monkeypatch.setattr(dbbrowser.scryfall, "getFormats", lambda: ["modern"])
    monkeypatch.setattr(dbbrowser.scryfall, "getTaggerTags", lambda: ([], []))

    parent = QtWidgets.QWidget()
    parent.proxyglyphFontId = 0
    parent.keyruneFontId = 0
    form = dbbrowser.SearchForm(parent=parent)
    form.testParent = parent
    form.show()
    qtApp.processEvents()
    searches = []
    form.searched.connect(searches.append)

    fields = [
        ("name", form.nameField),
        ("other type", form.otherTypeCB),
        ("oracle", form.oracleTextLE),
        ("cmc", form.cmcWidgetValue),
        ("price", form.priceWidgetValue),
    ]
    form.typeCB.setCurrentText("creature")
    qtApp.processEvents()
    fields.extend([
        ("power", form.creaturePowerWidgetLE),
        ("toughness", form.creatureToughnessWidgetLE),
    ])
    form.typeCB.setCurrentText("planeswalker")
    qtApp.processEvents()
    fields.append(("loyalty", form.planeswalkerLoyaltyWidgetLE))

    for label, field in fields:
        searches.clear()
        field.setFocus()
        QTest.keyClick(field, QtCore.Qt.Key.Key_Return)
        assert searches, f"Return did not trigger search for {label}"


def test_extras_checkbox_disabled_in_bulk_mode(qtApp, monkeypatch):
    monkeypatch.setattr(dbbrowser.constants, "USE_BULK_FILES", True)
    monkeypatch.setattr(
        dbbrowser.scryfall,
        "getSets",
        lambda: [{"id": "set-1", "code": "tst", "name": "Test Set", "released_at": "2024-01-01"}],
    )
    monkeypatch.setattr(dbbrowser.scryfall, "getSetReleaseYear", lambda setId: "2024")
    monkeypatch.setattr(dbbrowser.scryfall, "getFormats", lambda: ["modern"])
    monkeypatch.setattr(dbbrowser.scryfall, "getTaggerTags", lambda: ([], []))

    parent = QtWidgets.QWidget()
    parent.proxyglyphFontId = 0
    parent.keyruneFontId = 0
    form = dbbrowser.SearchForm(parent=parent)
    form.testParent = parent

    assert not form.extrasCB.isEnabled()


def test_clear_search_resets_fields(qtApp, monkeypatch):
    monkeypatch.setattr(
        dbbrowser.scryfall,
        "getSets",
        lambda: [{"id": "set-1", "code": "tst", "name": "Test Set", "released_at": "2024-01-01"}],
    )
    monkeypatch.setattr(dbbrowser.scryfall, "getSetReleaseYear", lambda setId: "2024")
    monkeypatch.setattr(dbbrowser.scryfall, "getFormats", lambda: ["modern"])
    monkeypatch.setattr(dbbrowser.scryfall, "getTaggerTags", lambda: ([], []))

    parent = QtWidgets.QWidget()
    parent.proxyglyphFontId = 0
    parent.keyruneFontId = 0
    form = dbbrowser.SearchForm(parent=parent)
    form.testParent = parent
    form.nameField.setText("bolt")
    form.typeCB.setCurrentText("creature")
    form.cmcWidgetValue.setText("10")
    form.paperCB.setChecked(False)
    cleared = []
    form.cleared.connect(lambda: cleared.append(True))

    form.clearSearch()

    assert form.nameField.text() == ""
    assert form.typeCB.currentText() == ""
    assert form.cmcWidgetValue.text() == ""
    assert form.paperCB.isChecked() is True
    assert cleared == [True]


def test_search_cleared_clears_results_and_invalidates_request(caplog):
    browser = SimpleNamespace(
        _searchRequestId=5,
        dbResultsList=DummyCardList(),
        resultsInfoLabel=DummyLabel(),
    )

    with caplog.at_level(logging.INFO):
        dbbrowser.DbBrowser.on_searchCleared(browser)

    assert browser._searchRequestId == 6
    assert browser.dbResultsList.cards == []
    assert browser.resultsInfoLabel.visible is False
    assert "Search cleared" in caplog.text


def test_search_buttons_are_outside_scroll_area(qtApp, monkeypatch):
    monkeypatch.setattr(
        dbbrowser.scryfall,
        "getSets",
        lambda: [{"id": "set-1", "code": "tst", "name": "Test Set", "released_at": "2024-01-01"}],
    )
    monkeypatch.setattr(dbbrowser.scryfall, "getSetReleaseYear", lambda setId: "2024")
    monkeypatch.setattr(dbbrowser.scryfall, "getFormats", lambda: ["modern"])
    monkeypatch.setattr(dbbrowser.scryfall, "getTaggerTags", lambda: ([], []))

    parent = QtWidgets.QWidget()
    parent.proxyglyphFontId = 0
    parent.keyruneFontId = 0
    browser = dbbrowser.DbBrowser(parent=parent)
    browser.testParent = parent

    assert browser.qscroll.widget() is browser.searchForm
    assert not browser.qscroll.isAncestorOf(browser.searchButton)
    assert browser.searchButtonsWidget.parent() is browser.searchPanel
