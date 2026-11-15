import logging

from lib import importexport


CARDS = {
    "cmd": {"id": "cmd", "name": "Nekusar, the Mindrazer", "set_name": "Commander 2013", "mtgo_id": 1},
    "bolt": {"id": "bolt", "name": "Lightning Bolt", "set_name": "Seventh Edition", "mtgo_id": 2},
    "pyro": {"id": "pyro", "name": "Pyroblast", "set_name": "Ice Age", "mtgo_id": 3},
}
SECTIONS = {
    "commander": [[1, "cmd"]],
    "main": [[4, "bolt"]],
    "sideboard": [[2, "pyro"]],
}


def lookup(cardId):
    return CARDS.get(cardId)


def test_cardmarket_export_is_flat_and_ordered():
    text = importexport.formatCardmarketExport(SECTIONS, cardLookup=lookup)

    assert text == (
        "1 Nekusar, the Mindrazer (Commander 2013)\n"
        "4 Lightning Bolt (Seventh Edition)\n"
        "2 Pyroblast (Ice Age)\n"
    )


def test_cardmarket_export_can_exclude_sections():
    text = importexport.formatCardmarketExport(
        SECTIONS, includeCommander=False, includeSideboard=False, cardLookup=lookup
    )

    assert text == "4 Lightning Bolt (Seventh Edition)\n"


def test_cardmarket_export_can_discard_set_info():
    text = importexport.formatCardmarketExport(SECTIONS, discardSet=True, cardLookup=lookup)

    assert "(" not in text
    assert "1 Nekusar, the Mindrazer" in text


def test_cardmarket_export_skips_missing_cards(caplog):
    with caplog.at_level(logging.WARNING):
        text = importexport.formatCardmarketExport(
            {"main": [[1, "missing"]]}, cardLookup=lookup
        )

    assert text == ""
    assert "Could not export card" in caplog.text


def test_export_dialog_defaults(qtApp, monkeypatch):
    monkeypatch.setattr(importexport.scryfall, "getCardById", lookup)
    dialog = importexport.exportDialog(SECTIONS)

    assert dialog.exportTypeSelector_cardmarketRB.isChecked()
    assert dialog.includeCommanderCB.isChecked()
    assert dialog.includeSideboardCB.isChecked()

    dialog.includeSideboardCB.setChecked(False)
    text = dialog.buildExportText()
    assert "Pyroblast" not in text
    assert "Nekusar" in text
    dialog.close()


def test_mtga_export_has_sections():
    text = importexport.formatMTGAExport(SECTIONS, cardLookup=lookup)

    assert text == (
        "Deck\n"
        "4 Lightning Bolt\n"
        "\n"
        "Sideboard\n"
        "2 Pyroblast\n"
        "\n"
        "Commander\n"
        "1 Nekusar, the Mindrazer\n"
    )


def test_mtgo_export_is_valid_dek_xml():
    from lxml import etree

    text = importexport.formatMTGOExport(SECTIONS, cardLookup=lookup)
    root = etree.fromstring(text.encode("utf-8"))
    cards = root.findall("Cards")

    assert len(cards) == 3
    assert cards[0].attrib["Name"] == "Lightning Bolt"
    assert cards[0].attrib["Sideboard"] == "false"
    assert cards[1].attrib["Name"] == "Pyroblast"
    assert cards[1].attrib["Sideboard"] == "true"


def test_plain_text_export_has_sections():
    text = importexport.formatPlainTextExport(SECTIONS, cardLookup=lookup)

    assert text == (
        "Commander\n"
        "1 Nekusar, the Mindrazer (Commander 2013)\n"
        "\n"
        "Main\n"
        "4 Lightning Bolt (Seventh Edition)\n"
        "\n"
        "Sideboard\n"
        "2 Pyroblast (Ice Age)\n"
    )


def test_export_dialog_switches_formats(qtApp, monkeypatch):
    monkeypatch.setattr(importexport.scryfall, "getCardById", lookup)
    dialog = importexport.exportDialog(SECTIONS)

    dialog.exportTypeSelector_mtgaRB.setChecked(True)
    assert dialog.buildExportText().startswith("Deck\n")

    dialog.exportTypeSelector_mtgoRB.setChecked(True)
    assert dialog.buildExportText().startswith("<?xml")

    dialog.exportTypeSelector_plainRB.setChecked(True)
    assert dialog.buildExportText().startswith("Commander\n")

    dialog.close()
