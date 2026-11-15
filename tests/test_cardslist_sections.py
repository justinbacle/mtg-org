import widgets.cardslist as cardslist


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
    monkeypatch.setattr(cardslist.deckrules, "validateDeck", lambda deck: [])

    widget.setCardStack(deck, "deck", "Test Deck")

    assert dummy.allowed == {"main", "sideboard", "commander"}
    assert dummy.sections["main"] == deck["cardList"]
    assert dummy.sections["sideboard"] == deck["sideboard"]
    assert dummy.sections["commander"] == deck["commander"]


def test_cardslist_limits_sections_by_format(qtApp, monkeypatch):
    widget = cardslist.CardsList()
    dummy = DummyTable()
    widget.cardsList = dummy
    monkeypatch.setattr(cardslist.deckrules, "validateDeck", lambda deck: [])

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
    assert dummy.allowed == {"main", "commander"}


def test_cardslist_collection_uses_main_only(qtApp, monkeypatch):
    widget = cardslist.CardsList()
    dummy = DummyTable()
    widget.cardsList = dummy
    monkeypatch.setattr(cardslist.deckrules, "validateDeck", lambda deck: [])
    collection = {"cardList": [[1, "card"]]}

    widget.setCardStack(collection, "collection", "Test Collection")

    assert dummy.allowed == {"main"}
    assert dummy.sections["main"] == collection["cardList"]
    assert dummy.showSectionHeaders is False
