import connector


def test_deck_sections_crud():
    name = "Deck Sections Test"
    connector.createDeck(name, [[1, "main-a"]], sideboard=[], commander=[])
    try:
        deck = connector.getDeck(name)
        assert deck["cardList"] == [[1, "main-a"]]
        assert deck["sideboard"] == []
        assert deck["commander"] == []

        connector.addCardToDeck(name, 1, "side-a", section="sideboard")
        connector.addCardToDeck(name, 2, "side-a", section="sideboard")
        connector.addCardToDeck(name, 1, "commander-a", section="commander")

        deck = connector.getDeck(name)
        assert deck["sideboard"] == [[3, "side-a"]]
        assert deck["commander"] == [[1, "commander-a"]]

        connector.changeCardDeckQty(name, 5, "side-a", section="sideboard")
        assert connector.getDeck(name)["sideboard"] == [[5, "side-a"]]

        connector.replaceCardInDeck(name, "side-a", "side-b", section="sideboard")
        assert connector.getDeck(name)["sideboard"] == [[5, "side-b"]]

        connector.removeCardFromDeck(name, "commander-a", section="commander")
        assert connector.getDeck(name)["commander"] == []
    finally:
        connector.removeDeck(name)


def test_old_deck_without_sections_still_works():
    name = "Old Deck Test"
    connector.getDB().table("Decks").insert({"name": name, "cardList": [[1, "old-card"]]})
    try:
        assert connector.getDeckSection(name, "main") == [[1, "old-card"]]

        connector.addCardToDeck(name, 1, "side-card", section="sideboard")
        assert connector.getDeckSection(name, "sideboard") == [[1, "side-card"]]
    finally:
        connector.removeDeck(name)


def test_deck_format_metadata():
    name = "Deck Format Test"
    connector.createDeck(name, format="modern")
    try:
        assert connector.getDeckFormat(name) == "modern"

        connector.setDeckFormat(name, "commander")
        assert connector.getDeckFormat(name) == "commander"

        connector.setDeckFormat(name, "not-a-format")
        assert connector.getDeckFormat(name) == "commander"
    finally:
        connector.removeDeck(name)


def test_move_card_between_sections():
    name = "Move Card Test"
    connector.createDeck(name, [[2, "card-a"]], sideboard=[[1, "card-b"]], commander=[])
    try:
        connector.moveCardInDeck(name, "card-a", "main", "sideboard")
        deck = connector.getDeck(name)
        assert deck["cardList"] == []
        assert deck["sideboard"] == [[1, "card-b"], [2, "card-a"]]

        connector.moveCardInDeck(name, "card-a", "sideboard", "commander")
        deck = connector.getDeck(name)
        assert deck["sideboard"] == [[1, "card-b"]]
        assert deck["commander"] == [[2, "card-a"]]
    finally:
        connector.removeDeck(name)


def test_deck_bracket_metadata():
    name = "Deck Bracket Test"
    connector.createDeck(name, format="commander", bracket=3)
    try:
        assert connector.getDeckBracket(name) == 3

        connector.setDeckBracket(name, 5)
        assert connector.getDeckBracket(name) == 5

        connector.setDeckBracket(name, 9)
        assert connector.getDeckBracket(name) == 5

        connector.setDeckFormat(name, "modern")
        connector.setDeckBracket(name, 3)
        assert connector.getDeckBracket(name) is None
    finally:
        connector.removeDeck(name)


def test_companion_section_crud():
    name = "Companion Section Test"
    connector.createDeck(name, format="commander", companion=[])
    try:
        connector.addCardToDeck(name, 1, "companion-card", section="companion")
        assert connector.getDeckSection(name, "companion") == [[1, "companion-card"]]

        connector.moveCardInDeck(name, "companion-card", "companion", "sideboard")
        assert connector.getDeckSection(name, "companion") == []
        assert connector.getDeckSection(name, "sideboard") == [[1, "companion-card"]]
    finally:
        connector.removeDeck(name)
