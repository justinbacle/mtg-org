import json

import constants
from PySide6 import QtWidgets
from widgets.cardlistwidget import CardSearchListWidget


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
