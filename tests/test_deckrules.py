import constants
from lib import deckrules


def makeDeck(formatKey, main=None, sideboard=None, commander=None, companion=None):
    return {
        "format": formatKey,
        "cardList": main or [],
        "sideboard": sideboard or [],
        "commander": commander or [],
        "companion": companion or [],
    }


def test_commander_requires_commander_and_100_cards(monkeypatch):
    monkeypatch.setattr(
        deckrules.scryfall,
        "getCardById",
        lambda cardId: {"id": cardId, "type_line": "Creature", "name": cardId},
    )
    deck = makeDeck("commander", main=[[99, "creature"]])
    details = deckrules.validateDeckDetails(deck)

    assert any("Select at least 1 commander" in message for message in details["issues"])
    assert any("need exactly 100" in message for message in details["issues"])
    assert any(issue["status"] == "✗ singleton" for issue in details["cards"])


def test_commander_sideboard_is_rejected():
    deck = makeDeck("commander", main=[[99, "creature"]], sideboard=[[1, "side"]])
    details = deckrules.validateDeckDetails(deck)

    assert any("Sideboard is not allowed" in message for message in details["issues"])


def test_constructed_sideboard_limit():
    deck = makeDeck("modern", main=[[60, "card"]], sideboard=[[16, "side"]])
    details = deckrules.validateDeckDetails(deck)

    assert any("maximum is 15" in message for message in details["issues"])


def test_constructed_commander_is_rejected():
    deck = makeDeck("standard", main=[[60, "card"]], commander=[[1, "commander"]])
    details = deckrules.validateDeckDetails(deck)

    assert any("Commanders are not allowed" in message for message in details["issues"])


def test_casual_deck_has_no_restrictions():
    deck = makeDeck("casual", main=[[1, "a"]], sideboard=[[30, "b"]], commander=[[1, "c"]])
    details = deckrules.validateDeckDetails(deck)
    assert details["issues"] == []
    assert details["cards"] == []


def test_singleton_allows_basic_lands(monkeypatch):
    def getCard(cardId):
        return {"id": cardId, "type_line": "Basic Land - Forest", "name": cardId}

    monkeypatch.setattr(deckrules.scryfall, "getCardById", getCard)
    deck = makeDeck("commander", main=[[30, "forest"]], commander=[[1, "commander"]])
    details = deckrules.validateDeckDetails(deck)

    assert not any(issue["status"] == "✗ singleton" for issue in details["cards"])


def test_allowed_sections_by_format():
    assert deckrules.allowedSections("modern") == {"main", "sideboard"}
    assert deckrules.allowedSections("commander") == {"main", "commander", "companion"}
    assert deckrules.allowedSections("casual") == {"main", "sideboard", "commander"}
    assert deckrules.allowedSections(constants.DEFAULT_DECK_FORMAT) == {
        "main",
        "sideboard",
        "commander",
    }


def card(cardId, name="Card", typeLine="Creature", oracleId=None, colors=None,
         keywords=None, text="", legalities=None, gameChanger=False):
    return {
        "id": cardId,
        "name": name,
        "type_line": typeLine,
        "oracle_id": oracleId or f"oracle-{cardId}",
        "color_identity": colors or [],
        "keywords": keywords or [],
        "oracle_text": text,
        "legalities": legalities or {},
        "game_changer": gameChanger,
    }


def test_four_of_rule(monkeypatch):
    cards = {
        "a": card("a", name="Lightning Bolt", oracleId="bolt",
                  legalities={"modern": "legal"}),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))
    deck = makeDeck("modern", main=[[5, "a"]])
    details = deckrules.validateDeckDetails(deck)

    assert any(
        issue["card"] == "Lightning Bolt" and issue["status"] == "✗ copies"
        for issue in details["cards"]
    )


def test_singleton_counts_printings_by_oracle(monkeypatch):
    cards = {
        "a": card("a", name="Sol Ring", oracleId="sol-ring"),
        "b": card("b", name="Sol Ring", oracleId="sol-ring"),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))
    deck = makeDeck("commander", main=[[1, "a"], [1, "b"]], commander=[[1, "cmd"]])
    details = deckrules.validateDeckDetails(deck)

    assert any(
        issue["card"] == "Sol Ring" and issue["status"] == "✗ singleton"
        for issue in details["cards"]
    )


def test_colour_identity(monkeypatch):
    cards = {
        "cmd": card("cmd", typeLine="Legendary Creature", colors=["U"]),
        "red": card("red", colors=["R"]),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))
    deck = makeDeck("commander", main=[[1, "red"]], commander=[[1, "cmd"]])
    details = deckrules.validateDeckDetails(deck)

    assert any("outside commander colour identity" in message for message in details["issues"])
    assert any(issue["status"] == "✗ identity" for issue in details["cards"])


def test_partner_pair_validation(monkeypatch):
    cards = {
        "a": card("a", typeLine="Legendary Creature", text="Partner"),
        "b": card("b", typeLine="Legendary Creature", text="Partner"),
        "c": card("c", typeLine="Legendary Creature"),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))

    valid = makeDeck("commander", main=[[98, "a"]], commander=[[1, "a"], [1, "b"]])
    invalid = makeDeck("commander", main=[[98, "a"]], commander=[[1, "a"], [1, "c"]])

    assert not any(
        "valid partner" in message for message in deckrules.validateDeckDetails(valid)["issues"]
    )
    assert any(
        "valid partner" in message for message in deckrules.validateDeckDetails(invalid)["issues"]
    )


def test_format_legality(monkeypatch):
    cards = {
        "banned": card("banned", name="Banned Card", legalities={"standard": "banned"}),
        "legal": card("legal", name="Legal Card", legalities={"standard": "legal"}),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))
    deck = makeDeck("standard", main=[[59, "legal"], [1, "banned"]])
    details = deckrules.validateDeckDetails(deck)

    assert any("Not legal in Standard: Banned Card (banned)" in message for message in details["issues"])
    assert any(issue["card"] == "Banned Card" and issue["status"] == "✗ legality" for issue in details["cards"])


def test_commander_bracket_game_changers(monkeypatch):
    cards = {
        "gc": card("gc", name="Rhystic Study", gameChanger=True),
        "normal": card("normal"),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))

    deck = makeDeck("commander", main=[[1, "gc"]], commander=[[1, "normal"]])
    deck["bracket"] = 2
    details = deckrules.validateDeckDetails(deck)
    assert details["bracket"]["floor"] == 3
    assert any("below the suggested minimum" in issue for issue in details["issues"])
    assert any(
        issue["card"] == "Rhystic Study" and issue["status"] == "✗ game changer"
        for issue in details["cards"]
    )

    deck["bracket"] = 3
    details = deckrules.validateDeckDetails(deck)
    assert not any("below the suggested minimum" in issue for issue in details["issues"])


def test_commander_bracket_extra_turns_and_mld(monkeypatch):
    cards = {
        "turn": card("turn", name="Time Warp", text="Take an extra turn after this one."),
        "mld": card("mld", name="Armageddon", text="Destroy all lands."),
        "cmd": card("cmd"),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))

    extra = makeDeck("commander", main=[[1, "turn"]], commander=[[1, "cmd"]])
    extra["bracket"] = 1
    extraDetails = deckrules.validateDeckDetails(extra)
    assert extraDetails["bracket"]["floor"] == 2
    assert any("Bracket 1 does not allow extra-turn" in issue for issue in extraDetails["issues"])
    assert any(
        issue["card"] == "Time Warp" and issue["status"] == "✗ extra turn"
        for issue in extraDetails["cards"]
    )

    mld = makeDeck("commander", main=[[1, "mld"]], commander=[[1, "cmd"]])
    mld["bracket"] = 3
    mldDetails = deckrules.validateDeckDetails(mld)
    assert mldDetails["bracket"]["floor"] == 4
    assert any("mass land denial" in issue for issue in mldDetails["issues"])
    assert any(
        issue["card"] == "Armageddon" and issue["status"] == "✗ land denial"
        for issue in mldDetails["cards"]
    )


def test_companion_validation(monkeypatch):
    cards = {
        "companion": card("companion", name="Lutri, the Spellchaser",
                          text="Companion — Your starting deck contains only cards with even mana values."),
        "not-companion": card("not-companion", name="Sol Ring"),
        "commander": card("commander", text=""),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))

    valid = makeDeck("commander", main=[[99, "commander"]], commander=[[1, "commander"]],
                     companion=[[1, "companion"]])
    valid["bracket"] = None
    assert not any("not a companion" in issue for issue in deckrules.validateDeckDetails(valid)["issues"])

    invalid = makeDeck("commander", main=[[99, "commander"]], commander=[[1, "commander"]],
                       companion=[[1, "not-companion"]])
    invalid["bracket"] = None
    details = deckrules.validateDeckDetails(invalid)
    assert any("not a companion" in issue for issue in details["issues"])


def test_multiple_companions_rejected(monkeypatch):
    cards = {
        "companion": card("companion", name="Lutri", text="Companion — test"),
        "commander": card("commander"),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))
    deck = makeDeck("commander", main=[[99, "commander"]], commander=[[1, "commander"]],
                    companion=[[1, "companion"], [1, "companion"]])
    details = deckrules.validateDeckDetails(deck)
    assert any("only have one companion" in issue for issue in details["issues"])


def test_commander_bracket_detects_combo(monkeypatch):
    cards = {
        "oracle": card("oracle", name="Thassa's Oracle", text="Companion"),
        "consult": card("consult", name="Demonic Consultation", text="Search your library"),
        "cmd": card("cmd"),
    }
    monkeypatch.setattr(deckrules.scryfall, "getCardById", lambda cardId: cards.get(cardId))
    deck = makeDeck("commander", main=[[1, "oracle"], [1, "consult"]], commander=[[1, "cmd"]])
    deck["bracket"] = 2

    details = deckrules.validateDeckDetails(deck)
    analysis = details["bracket"]

    assert analysis["floor"] == 3
    assert analysis["possibleCombos"] == ["Thassa's Oracle + Demonic Consultation"]
    assert any("intentional two-card combos" in issue for issue in details["issues"])
    assert any("combo timing" in guidance for guidance in analysis["guidance"])
    assert any(
        issue["card"] == "Thassa's Oracle" and issue["status"] == "✗ combo"
        for issue in details["cards"]
    )
    assert any(
        issue["card"] == "Demonic Consultation" and issue["status"] == "✗ combo"
        for issue in details["cards"]
    )
