from lib import advisor


def card(cardId, name, typeLine="Creature", cmc=2.0):
    return {"id": cardId, "name": name, "type_line": typeLine, "cmc": cmc}


def lookup(cardId):
    return {
        "cmd": card("cmd", "Test Commander", "Legendary Creature", 4.0),
        "land": card("land", "Island", "Basic Land — Island", 0.0),
        "two": card("two", "Two Drop", "Creature", 2.0),
        "four": card("four", "Four Drop", "Creature", 4.0),
    }.get(cardId)


def test_commander_land_floor_and_model_target():
    deck = {
        "format": "commander",
        "commander": [[1, "cmd"]],
        "cardList": [[30, "land"], [1, "two"]],
    }

    findings = advisor.analyzeCommander(deck, lookup)
    text = "\n".join(finding["text"] for finding in findings)

    assert "Fewer than 37 lands" in text
    assert "39 lands" in text
    assert "You currently run 30 lands" in text


def test_commander_curve_target_and_commander_mv_tip():
    deck = {
        "format": "commander",
        "commander": [[1, "cmd"]],
        "cardList": [[39, "land"], [1, "four"]],
    }

    findings = advisor.analyzeCommander(deck, lookup)
    text = "\n".join(finding["text"] for finding in findings)

    assert "1/2/3/4/5/6 drops" in text
    assert "zero cards at that mana value" in text


def test_non_commander_has_no_advisor_findings():
    assert advisor.analyzeCommander({"format": "modern", "cardList": []}, lookup) == []


def test_commander_color_sources_report_missing_lands():
    cards = {
        "cmd": {"id": "cmd", "name": "Gold Commander", "type_line": "Legendary Creature", "cmc": 4.0,
                "mana_cost": "{1}{W}{U}{U}", "colors": ["W", "U"]},
        "white": {"id": "white", "name": "Double White", "type_line": "Creature", "cmc": 3.0,
                  "mana_cost": "{1}{W}{W}", "colors": ["W"]},
        "land": {"id": "land", "name": "Azorius Land", "type_line": "Land", "cmc": 0.0,
                 "produced_mana": ["W", "U"]},
    }
    deck = {
        "format": "commander",
        "commander": [[1, "cmd"]],
        "cardList": [[1, "land"], [1, "white"]],
    }

    findings = advisor.analyzeCommander(deck, cards.get)
    text = "\n".join(finding["text"] for finding in findings)

    assert "Blue: 1 / 29 land sources" in text
    assert "White: 1 / 28 land sources" in text
    assert any(finding.get("details") for finding in findings)


def test_commander_curve_target_matches_source_table():
    deck = {
        "format": "commander",
        "commander": [[1, "cmd"]],
        "cardList": [],
    }

    assert advisor.commanderCurveTarget(deck, lookup) == [6, 12, 13, 0, 13, 8]
