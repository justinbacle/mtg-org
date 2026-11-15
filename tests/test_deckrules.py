import constants
from lib import deckrules


def makeDeck(formatKey, main=None, sideboard=None, commander=None):
    return {
        "format": formatKey,
        "cardList": main or [],
        "sideboard": sideboard or [],
        "commander": commander or [],
    }


def test_commander_requires_commander_and_100_cards(monkeypatch):
    monkeypatch.setattr(
        deckrules.scryfall,
        "getCardById",
        lambda cardId: {"id": cardId, "type_line": "Creature", "name": cardId},
    )
    deck = makeDeck("commander", main=[[99, "creature"]])
    messages = deckrules.validateDeck(deck)

    assert any("Select at least 1 commander" in message for message in messages)
    assert any("need exactly 100" in message for message in messages)
    assert any("Singleton rule" in message for message in messages)


def test_commander_sideboard_is_rejected():
    deck = makeDeck("commander", main=[[99, "creature"]], sideboard=[[1, "side"]])
    messages = deckrules.validateDeck(deck)

    assert any("Sideboard is not allowed" in message for message in messages)


def test_constructed_sideboard_limit():
    deck = makeDeck("modern", main=[[60, "card"]], sideboard=[[16, "side"]])
    messages = deckrules.validateDeck(deck)

    assert any("maximum is 15" in message for message in messages)


def test_constructed_commander_is_rejected():
    deck = makeDeck("standard", main=[[60, "card"]], commander=[[1, "commander"]])
    messages = deckrules.validateDeck(deck)

    assert any("Commanders are not allowed" in message for message in messages)


def test_casual_deck_has_no_restrictions():
    deck = makeDeck("casual", main=[[1, "a"]], sideboard=[[30, "b"]], commander=[[1, "c"]])
    assert deckrules.validateDeck(deck) == []


def test_singleton_allows_basic_lands(monkeypatch):
    def getCard(cardId):
        return {"id": cardId, "type_line": "Basic Land - Forest", "name": cardId}

    monkeypatch.setattr(deckrules.scryfall, "getCardById", getCard)
    deck = makeDeck("commander", main=[[30, "forest"]], commander=[[1, "commander"]])
    messages = deckrules.validateDeck(deck)

    assert not any("Singleton rule" in message for message in messages)


def test_allowed_sections_by_format():
    assert deckrules.allowedSections("modern") == {"main", "sideboard"}
    assert deckrules.allowedSections("commander") == {"main", "commander"}
    assert deckrules.allowedSections("casual") == {"main", "sideboard", "commander"}
    assert deckrules.allowedSections(constants.DEFAULT_DECK_FORMAT) == {
        "main",
        "sideboard",
        "commander",
    }
