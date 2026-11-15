import json

import constants
from PySide6 import QtWidgets
from widgets.cardlistwidget import COLUMN_MAX_WIDTHS, CardSearchListWidget


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
