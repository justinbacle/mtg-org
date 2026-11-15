import logging

from lib import importexport


CARDS = {
    "cmd": {"id": "cmd", "name": "Nekusar, the Mindrazer", "set_name": "Commander 2013", "mtgo_id": 1},
    "bolt": {"id": "bolt", "name": "Lightning Bolt", "set_name": "Seventh Edition", "mtgo_id": 2},
    "pyro": {"id": "pyro", "name": "Pyroblast", "set_name": "Ice Age", "mtgo_id": 3},
    "cmp": {"id": "cmp", "name": "Lutri, the Spellchaser", "set_name": "Ikoria", "mtgo_id": 4},
}
SECTIONS = {
    "commander": [[1, "cmd"]],
    "main": [[4, "bolt"]],
    "sideboard": [[2, "pyro"]],
}
COMPANION_SECTIONS = {
    **SECTIONS,
    "companion": [[1, "cmp"]],
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
    assert not dialog.sectionsGB.isHidden()

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


def test_companion_export_in_flat_and_sectioned_formats():
    cardmarket = importexport.formatCardmarketExport(COMPANION_SECTIONS, cardLookup=lookup)
    assert "Lutri, the Spellchaser" in cardmarket

    mtga = importexport.formatMTGAExport(COMPANION_SECTIONS, cardLookup=lookup)
    assert "Companion\n1 Lutri, the Spellchaser" in mtga

    plain = importexport.formatPlainTextExport(COMPANION_SECTIONS, cardLookup=lookup)
    assert "Companion\n1 Lutri, the Spellchaser" in plain

    from lxml import etree
    mtgo = importexport.formatMTGOExport(COMPANION_SECTIONS, cardLookup=lookup)
    root = etree.fromstring(mtgo.encode("utf-8"))
    companion = [card for card in root.findall("Cards") if card.attrib["Name"] == "Lutri, the Spellchaser"]
    assert len(companion) == 1
    assert companion[0].attrib["Sideboard"] == "true"


def test_companion_export_can_be_excluded():
    text = importexport.formatCardmarketExport(
        COMPANION_SECTIONS, includeCompanion=False, cardLookup=lookup
    )
    assert "Lutri" not in text


def test_export_dialog_includes_companion_checkbox(qtApp, monkeypatch):
    monkeypatch.setattr(importexport.scryfall, "getCardById", lookup)
    dialog = importexport.exportDialog(COMPANION_SECTIONS)
    assert dialog.includeCompanionCB.isChecked()
    assert dialog.includeCompanionCB.isVisible() or not dialog.includeCompanionCB.isHidden()


def test_mtgo_export_dialog_documents_commander_zone_limitation(qtApp, monkeypatch):
    monkeypatch.setattr(importexport.scryfall, "getCardById", lookup)
    dialog = importexport.exportDialog(SECTIONS)

    dialog.exportTypeSelector_mtgoRB.setChecked(True)
    assert not dialog.mtgoWarningLabel.isHidden()
    assert "no commander zone" in dialog.mtgoWarningLabel.text()

    dialog.exportTypeSelector_mtgaRB.setChecked(True)
    assert dialog.mtgoWarningLabel.isHidden()
    dialog.close()


def test_mtgo_export_dialog_documents_companion_zone_limitation(qtApp, monkeypatch):
    monkeypatch.setattr(importexport.scryfall, "getCardById", lookup)
    dialog = importexport.exportDialog(COMPANION_SECTIONS)

    dialog.exportTypeSelector_mtgoRB.setChecked(True)
    text = dialog.mtgoWarningLabel.text()
    assert "no commander zone" in text
    assert "no companion zone" in text

    dialog.includeCompanionCB.setChecked(False)
    assert "no companion zone" not in dialog.mtgoWarningLabel.text()
    dialog.close()
