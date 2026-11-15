import widgets.cardslist as cardslist
import widgets.deckselector as deckselector
from lib import deckrules


class DummyTable:
    def __init__(self):
        self.addSection = None
        self.sections = None
        self.allowed = None
        self.sectionCardStacks = {}

    def setSections(self, sections, allowed, showSectionHeaders=True):
        self.sections = sections
        self.allowed = allowed
        self.showSectionHeaders = showSectionHeaders
        self.sectionCardStacks = sections

    def renderSections(self):
        ...


def test_cardslist_sends_all_deck_sections(qtApp, monkeypatch):
    widget = cardslist.CardsList()
    dummy = DummyTable()
    widget.cardsList = dummy
    deck = {
        "format": "casual",
        "cardList": [[1, "main-card"]],
        "sideboard": [[2, "side-card"]],
        "commander": [[1, "commander-card"]],
    }
    monkeypatch.setattr(cardslist.connector, "getDeck", lambda name: deck)
    monkeypatch.setattr(cardslist.deckrules, "validateDeckDetails", lambda deck: {
        "format": deck.get("format", "casual"), "label": "Casual", "issues": [], "cards": [],
    })

    widget.setCardStack(deck, "deck", "Test Deck")

    assert dummy.allowed == {"main", "sideboard", "commander"}
    assert dummy.sections["main"] == deck["cardList"]
    assert dummy.sections["sideboard"] == deck["sideboard"]
    assert dummy.sections["commander"] == deck["commander"]


def test_cardslist_limits_sections_by_format(qtApp, monkeypatch):
    widget = cardslist.CardsList()
    dummy = DummyTable()
    widget.cardsList = dummy
    monkeypatch.setattr(cardslist.deckrules, "validateDeckDetails", lambda deck: {
        "format": deck.get("format", "casual"), "label": "Casual", "issues": [], "cards": [],
    })

    modern = {
        "format": "modern",
        "cardList": [],
        "sideboard": [],
        "commander": [],
    }
    monkeypatch.setattr(cardslist.connector, "getDeck", lambda name: modern)
    widget.setCardStack(modern, "deck", "Modern Deck")
    assert dummy.allowed == {"main", "sideboard"}

    commander = {
        "format": "commander",
        "cardList": [],
        "sideboard": [],
        "commander": [],
    }
    monkeypatch.setattr(cardslist.connector, "getDeck", lambda name: commander)
    widget.setCardStack(commander, "deck", "Commander Deck")
    assert dummy.allowed == {"main", "commander", "companion"}


def test_cardslist_collection_uses_main_only(qtApp, monkeypatch):
    widget = cardslist.CardsList()
    dummy = DummyTable()
    widget.cardsList = dummy
    monkeypatch.setattr(cardslist.deckrules, "validateDeckDetails", lambda deck: {
        "format": deck.get("format", "casual"), "label": "Casual", "issues": [], "cards": [],
    })
    collection = {"cardList": [[1, "card"]]}

    widget.setCardStack(collection, "collection", "Test Collection")

    assert dummy.allowed == {"main"}
    assert dummy.sections["main"] == collection["cardList"]
    assert dummy.showSectionHeaders is False


def test_format_legality_widget_shows_issues(qtApp):
    widget = cardslist.FormatLegalityWidget()
    widget.setDetails({
        "format": "commander",
        "label": "Commander",
        "issues": ["Deck has 97 cards; minimum is 100."],
        "cards": [
            {"card": "Lightning Bolt", "status": "✗ identity", "reason": "R not in UBR"},
        ],
    })

    assert widget.isVisible() is False or widget.isHidden() is False
    assert widget.table.rowCount() == 2
    assert widget.table.item(0, 0).text() == "Deck"
    assert widget.table.item(1, 0).text() == "Lightning Bolt"
    assert widget.table.item(1, 1).text() == "✗ identity"
    assert widget.statusButton.text() == "2 issue(s)"
    assert widget.bracketLabel.isHidden()

    widget.setDetails({
        "format": "commander",
        "label": "Commander",
        "issues": [],
        "cards": [],
    })
    assert widget.table.rowCount() == 1
    assert widget.table.item(0, 1).text() == "✓"
    assert widget.statusButton.text() == "Legal"

    widget.setDetails(None)
    assert widget.isHidden()


def test_format_legality_widget_shows_bracket(qtApp):
    widget = cardslist.FormatLegalityWidget()
    widget.setDetails({
        "format": "commander",
        "label": "Commander",
        "issues": [],
        "cards": [],
        "bracket": {
            "floor": 3,
            "selected": 2,
            "gameChangers": ["Rhystic Study"],
            "extraTurns": [],
            "massLandDenial": [],
            "tutors": [],
            "infinite": [],
        },
    })

    assert not widget.bracketLabel.isHidden()
    assert "suggested minimum Bracket 3" in widget.bracketLabel.text()


def test_deck_dialog_bracket_only_for_commander(qtApp):
    from widgets.deckselector import DeckDialog

    dialog = DeckDialog(formatKey="commander", bracket=3)
    assert dialog.values()[2] == 3

    dialog.formatCB.setCurrentIndex(dialog.formatCB.findData("modern"))
    assert dialog.values()[2] is None


def test_deck_dialog_keeps_bracket_suggestion(qtApp, monkeypatch):
    card = {
        "id": "gc",
        "name": "Rhystic Study",
        "oracle_id": "rhystic",
        "type_line": "Enchantment",
        "color_identity": ["U"],
        "legalities": {},
        "game_changer": True,
    }
    monkeypatch.setattr(
        deckrules.scryfall,
        "getCardById",
        lambda cardId: card if cardId == "gc" else None,
    )
    deck = {
        "format": "commander",
        "cardList": [[1, "gc"]],
        "sideboard": [],
        "commander": [],
    }

    dialog = deckselector.DeckDialog(formatKey="commander", bracket=2, deck=deck)

    assert "Suggested minimum: Bracket 3" in dialog.estimateLabel.text()
    assert "Selected bracket 2 is below" in dialog.estimateLabel.text()


def test_cardslist_applies_set_to_collection(qtApp, monkeypatch):
    widget = cardslist.CardsList()
    widget.cardsList = DummyTable()
    widget.stackType = "collection"
    widget.stackName = "Test Collection"
    calls = []
    monkeypatch.setattr(
        cardslist.connector,
        "replaceCardInCollection",
        lambda name, oldId, newId: calls.append((name, oldId, newId)),
    )
    widget.cardsList.reloadFromDatabase = lambda: calls.append(("reload",))

    widget.replaceCardInAnySection("old-id", "new-id")

    assert calls == [
        ("Test Collection", "old-id", "new-id"),
        ("reload",),
    ]
