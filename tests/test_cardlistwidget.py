import json

import constants
from PySide6 import QtCore, QtGui, QtWidgets
from widgets.cardlistwidget import COLUMN_MAX_WIDTHS, CardSearchListWidget, CardStackListWidget


def makeWidget(qtApp):
    parent = QtWidgets.QWidget()
    parent.keyruneFontId = 0
    parent.proxyglyphFontId = 0
    parent.phyrexianFontId = 0
    widget = CardSearchListWidget(parent)
    widget.testParent = parent
    return widget


def test_unknown_keyrune_set_falls_back_to_code(tmp_path, monkeypatch, qtApp):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "keyrune.json").write_text(json.dumps({"2ed": "&#xe602;"}))
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", fonts)

    widget = makeWidget(qtApp)
    item = widget.getCardTableItem({"set": "slc"}, columns=["set"])[0]

    assert item.text() == "SLC"


def test_known_keyrune_set_uses_glyph(tmp_path, monkeypatch, qtApp):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "keyrune.json").write_text(json.dumps({"2ed": "&#xe602;"}))
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", fonts)

    widget = makeWidget(qtApp)
    item = widget.getCardTableItem({"set": "2ed"}, columns=["set"])[0]

    assert item.text() == "\ue602"


def test_missing_keyrune_file_does_not_crash(tmp_path, monkeypatch, qtApp):
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", tmp_path / "missing")

    widget = makeWidget(qtApp)
    item = widget.getCardTableItem({"set": "slc"}, columns=["set"])[0]

    assert item.text() == "SLC"


def test_table_columns_are_capped(tmp_path, monkeypatch, qtApp):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "keyrune.json").write_text(json.dumps({"tst": "&#xe602;"}))
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", fonts)

    parent = QtWidgets.QWidget()
    parent.keyruneFontId = 0
    parent.proxyglyphFontId = 0
    parent.phyrexianFontId = 0
    widget = CardSearchListWidget(parent)
    widget.testParent = parent
    card = {
        "id": "card-1",
        "name": "Terra, Magical Adept // Esper Terra",
        "mana_cost": "{2}{W}{U}",
        "type_line": "Legendary Creature - Human Wizard // Legendary Creature - Human Wizard Warrior",
        "set": "tst",
        "rarity": "rare",
        "prices": {"eur": "1.00"},
    }

    widget.setCards([(1, card)])

    typeColumn = widget.columns.index("type_line")
    nameColumn = widget.columns.index("name")
    assert widget.columnWidth(typeColumn) <= COLUMN_MAX_WIDTHS["type_line"]
    assert widget.columnWidth(nameColumn) <= COLUMN_MAX_WIDTHS["name"]


def test_stack_table_renders_section_headers(tmp_path, monkeypatch, qtApp):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "keyrune.json").write_text(json.dumps({"tst": "&#xe602;"}))
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", fonts)

    parent = QtWidgets.QWidget()
    parent.keyruneFontId = 0
    parent.proxyglyphFontId = 0
    parent.phyrexianFontId = 0
    widget = CardStackListWidget(parent)
    widget.testParent = parent
    card = {
        "id": "card-1",
        "name": "Test Card",
        "mana_cost": "{1}",
        "type_line": "Instant",
        "set": "tst",
        "rarity": "common",
        "prices": {"eur": "1.00"},
    }
    widget.sectionCardStacks = {
        "main": [(1, dict(card))],
        "sideboard": [(2, dict(card, id="card-2"))],
        "commander": [],
    }
    widget.visibleSections = ["commander", "main", "sideboard"]

    widget.renderSections()

    assert widget.item(0, 0).text() == "Commander (0)"
    assert widget.item(1, 0).text() == "Main (1)"
    assert widget.item(3, 0).text() == "Sideboard (2)"
    assert widget.rowSections[2] == "main"
    assert widget.rowSections[4] == "sideboard"
    palette = widget.palette()
    assert widget.item(1, 0).background().color() == palette.color(QtGui.QPalette.ColorRole.AlternateBase)
    assert widget.item(1, 0).foreground().color() == palette.color(QtGui.QPalette.ColorRole.Text)


def test_stack_table_can_render_without_section_headers(tmp_path, monkeypatch, qtApp):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "keyrune.json").write_text(json.dumps({"tst": "&#xe602;"}))
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", fonts)
    parent = QtWidgets.QWidget()
    parent.keyruneFontId = 0
    parent.proxyglyphFontId = 0
    parent.phyrexianFontId = 0
    widget = CardStackListWidget(parent)
    widget.testParent = parent
    card = {
        "id": "card-1",
        "name": "Test Card",
        "mana_cost": "{1}",
        "type_line": "Instant",
        "set": "tst",
        "rarity": "common",
        "prices": {"eur": "1.00"},
    }
    widget.showSectionHeaders = False
    widget.visibleSections = ["main"]
    widget.sectionCardStacks = {"main": [(1, card)]}

    widget.renderSections()

    assert widget.item(0, 0).text() == "1"
    assert widget.rowSections[0] == "main"


def test_move_card_to_section(qtApp, monkeypatch):
    from types import SimpleNamespace
    import widgets.cardlistwidget as cardlistwidget

    parent = QtWidgets.QWidget()
    parent.keyruneFontId = 0
    parent.proxyglyphFontId = 0
    parent.phyrexianFontId = 0
    parent.deckSelector = SimpleNamespace(getSelected=lambda: ("deck", "Test Deck"))
    widget = CardStackListWidget(parent)
    widget.testParent = parent
    widget.setRowCount(1)
    item = QtWidgets.QTableWidgetItem("1")
    item.setData(
        QtCore.Qt.ItemDataRole.UserRole,
        {"data": {"id": "card-1"}, "column": "qty"},
    )
    widget.setItem(0, 0, item)
    widget.rowSections = {0: "main"}
    calls = []
    monkeypatch.setattr(
        cardlistwidget.connector,
        "moveCardInDeck",
        lambda deckName, cardId, fromSection, toSection: calls.append(
            (deckName, cardId, fromSection, toSection)
        ),
    )
    monkeypatch.setattr(widget, "reloadFromDatabase", lambda: None)

    widget.moveCardToSection(0, "sideboard")

    assert calls == [("Test Deck", "card-1", "main", "sideboard")]


def test_sort_sections_by_name_and_price(tmp_path, monkeypatch, qtApp):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "keyrune.json").write_text(json.dumps({"tst": "&#xe602;"}))
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", fonts)
    parent = QtWidgets.QWidget()
    parent.keyruneFontId = 0
    parent.proxyglyphFontId = 0
    parent.phyrexianFontId = 0
    widget = CardStackListWidget(parent)
    widget.testParent = parent
    widget.showSectionHeaders = False

    def card(cardId, name, price):
        return {
            "id": cardId,
            "name": name,
            "mana_cost": "{1}",
            "type_line": "Instant",
            "set": "tst",
            "rarity": "common",
            "prices": {"eur": price},
        }

    widget.sectionCardStacks = {
        "main": [(1, card("b", "Beta", "5")), (1, card("a", "Alpha", "1"))],
    }
    widget.visibleSections = ["main"]

    widget.sortSections("name")
    assert [entry[1]["name"] for entry in widget.sectionCardStacks["main"]] == ["Alpha", "Beta"]

    widget.sortSections("prices")
    assert [entry[1]["name"] for entry in widget.sectionCardStacks["main"]] == ["Alpha", "Beta"]


def test_invalid_qty_edit_is_reverted(qtApp):
    parent = QtWidgets.QWidget()
    widget = CardStackListWidget(parent)
    widget.testParent = parent
    widget.setRowCount(1)
    item = QtWidgets.QTableWidgetItem("2")
    item.setData(
        QtCore.Qt.ItemDataRole.UserRole,
        {"data": {"qty": 2}, "column": "qty"},
    )
    widget.setItem(0, 0, item)
    item.setText("")

    widget.on_itemChanged(item)

    assert item.text() == "2"
