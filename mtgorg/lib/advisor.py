"""Deck advisor rules backed by published sources.

Commander thresholds and curve targets come from Frank Karsten's
"What's an Optimal Mana Curve and Land/Ramp Count for Commander?"
https://www.tcgplayer.com/content/article/What-s-an-Optimal-Mana-Curve-and-Land-Ramp-Count-for-Commander/e22caad1-b04b-4f8a-951b-a41e9f08da14/
"""

import re

from lib import oracletags

SOURCE = (
    "https://www.tcgplayer.com/content/article/"
    "What-s-an-Optimal-Mana-Curve-and-Land-Ramp-Count-for-Commander/"
    "e22caad1-b04b-4f8a-951b-a41e9f08da14/"
)
SOURCE_LABEL = "Frank Karsten, TCGplayer"
SOURCE_SOURCES = (
    "https://www.tcgplayer.com/content/article/"
    "How-Many-Sources-Do-You-Need-to-Consistently-Cast-Your-Spells-A-2022-Update/"
    "dc23a7d2-0a16-4c0b-ad36-586fcca03ad8/"
)
SOURCE_SOURCES_LABEL = "Frank Karsten, 2022 source analysis"

SOURCE_REQUIREMENTS_99 = {
    "C": 19, "1C": 19, "2C": 18, "3C": 16, "4C": 15, "5C": 14,
    "CC": 30, "1CC": 28, "2CC": 26, "3CC": 23, "4CC": 22, "5CC": 20,
    "CCC": 36, "1CCC": 33, "2CCC": 30, "3CCC": 28, "4CCC": 26,
    "CCCC": 39, "1CCCC": 36,
}

LAND_TARGETS = {
    2: {"lands": 42, "rocks": 0},
    3: {"lands": 42, "rocks": 0},
    4: {"lands": 39, "rocks": 7},
    5: {"lands": 39, "rocks": 8},
    6: {"lands": 38, "rocks": 9},
}

COLOR_NAMES = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}
SOURCE_TAGS = "https://scryfall.com/docs/tagger-tags"
SOURCE_TAGS_LABEL = "Scryfall Tagger"
TAG_CATEGORIES = {
    "Ramp": {
        "ramp", "land ramp", "combat ramp", "multi land ramp", "ramp with set's mechanic",
        "mana rock", "utility mana rock", "mana rock with set's mechanic",
        "mana dork", "mana dork egg",
    },
    "Card draw": {
        "draw engine", "burst draw", "pure draw", "repeatable draw",
        "repeatable pure draw", "impulsive draw", "repeatable impulsive draw",
        "long term impulsive draw", "draw to seven",
    },
    "Spot removal": {"spot removal"},
    "Board wipes": {"sweeper", "sweeper-one-sided"},
    "Counterspells": {"counterspell-prefix"},
    "Tutors": {"tutor-to-hand", "tutors-by-name", "tutor-prefix"},
    "Protection": {"gives protection", "gives player protection", "protects-prefix"},
    "Graveyard hate": {"hate-graveyard", "hate-graveyard-cast", "single-minded graveyard hate"},
}

CURVE_TARGETS = {
    2: [9, 0, 20, 14, 9, 4],
    3: [8, 19, 0, 16, 10, 3],
    4: [6, 12, 13, 0, 13, 8],
    5: [6, 12, 10, 13, 0, 10],
    6: [6, 12, 10, 14, 9, 0],
}


def _finding(severity: str, text: str, source: str = SOURCE,
             sourceLabel: str = SOURCE_LABEL) -> dict:
    return {"severity": severity, "text": text, "source": source, "sourceLabel": sourceLabel}


def _commanderCards(deck: dict) -> list[dict]:
    return [entry for entry in deck.get("commander", [])]


def _landCount(entries: list, cardLookup) -> int:
    lands = 0
    for qty, cardId in entries:
        card = cardLookup(cardId)
        if card is not None and "Land" in str(card.get("type_line", "")):
            lands += qty
    return lands


def _isTappedLand(card: dict) -> bool:
    text = str(card.get("oracle_text", "")).lower()
    return "enters the battlefield tapped" in text or "enters tapped" in text


def _landSources(entries: list, cardLookup) -> tuple[dict[str, int], dict[str, int]]:
    allSources = dict.fromkeys("WUBRG", 0)
    untappedSources = dict.fromkeys("WUBRG", 0)
    for qty, cardId in entries:
        card = cardLookup(cardId)
        if card is None or "Land" not in str(card.get("type_line", "")):
            continue
        produced = card.get("produced_mana") or []
        untapped = not _isTappedLand(card)
        for color in produced:
            if color in allSources:
                allSources[color] += qty
                if untapped:
                    untappedSources[color] += qty
    return allSources, untappedSources


def _sourceRequirement(card: dict) -> dict[str, tuple[int, str, bool]]:
    """Return {color: (required, example cost, untappedOnly)} for a regular spell."""
    cost = str(card.get("mana_cost") or "")
    if not cost or "//" in cost:
        return {}
    pips: dict[str, int] = {}
    generic = 0
    for token in re.findall(r"\{([^}]+)\}", cost):
        if token in "WUBRG":
            pips[token] = pips.get(token, 0) + 1
        elif token.isdigit():
            generic += int(token)
        elif token in ("X", "Y", "Z", "S", "C"):
            continue
        else:
            return {}
    if not pips:
        return {}
    required = {}
    for color, pipCount in pips.items():
        if pipCount > 4:
            continue
        key = f"{generic}{'C' * pipCount}" if generic or pipCount > 1 else "C"
        if key not in SOURCE_REQUIREMENTS_99:
            continue
        value = SOURCE_REQUIREMENTS_99[key]
        if len(pips) > 1:
            value += 1
        required[color] = (value, cost, key == "C")
    return required


def analyzeCommander(deck: dict, cardLookup) -> list[dict]:
    """Return sourced Advisor findings for a Commander deck."""
    if deck.get("format") != "commander":
        return []
    cardCache: dict[str, dict | None] = {}

    def lookup(cardId):
        if cardId not in cardCache:
            cardCache[cardId] = cardLookup(cardId)
        return cardCache[cardId]

    findings = []
    mainEntries = deck.get("cardList", [])
    commanderCards = [lookup(entry[1]) for entry in _commanderCards(deck)]
    commanderCards = [card for card in commanderCards if card is not None]
    lands = _landCount(mainEntries, lookup)
    findings.append(_finding(
        "info",
        f"Land count: {lands}. The model's target depends on your commander's mana value.",
    ))

    if lands < 37:
        findings.append(_finding(
            "warning",
            "Fewer than 37 lands. For medium-power midrange Commander decks, the article advises "
            "not going below 37.",
        ))

    if len(commanderCards) == 1:
        commander = commanderCards[0]
        mv = commander.get("cmc")
        if mv is not None and int(mv) in LAND_TARGETS:
            mv = int(mv)
            target = LAND_TARGETS[mv]
            rocks = "Sol Ring + 0 Signets" if target["rocks"] == 0 else f"Sol Ring + {target['rocks']} Signets"
            findings.append(_finding(
                "info" if lands >= target["lands"] else "warning",
                f"Commander with mana value {mv}: model target is {target['lands']} lands with {rocks}. "
                f"You currently run {lands} lands.",
            ))
            targetCurve = "/".join(str(value) for value in CURVE_TARGETS[mv])
            findings.append(_finding(
                "info",
                f"Model curve for a commander with mana value {mv} (1/2/3/4/5/6 drops): {targetCurve}.",
            ))
            sameMv = 0
            for qty, cardId in mainEntries:
                card = cardLookup(cardId)
                if card is None or "Land" in str(card.get("type_line", "")):
                    continue
                if card.get("cmc") is not None and int(card["cmc"]) == mv:
                    sameMv += qty
            if sameMv:
                findings.append(_finding(
                    "tip",
                    f"You run {sameMv} card(s) at your commander's mana value ({mv}). "
                    "The optimized model contains zero cards at that mana value.",
                ))
        elif mv is not None:
            findings.append(_finding(
                "info",
                f"Commander mana value {int(mv)} is outside the article's 2–6 mana table.",
            ))

    spellCards = []
    for qty, cardId in mainEntries:
        card = lookup(cardId)
        if card is not None and "Land" not in str(card.get("type_line", "")):
            spellCards.append(card)
    spellCards.extend(commanderCards)
    requirements: dict[str, list[tuple[int, str, str, bool]]] = {}
    for card in spellCards:
        for color, (required, cost, untappedOnly) in _sourceRequirement(card).items():
            requirements.setdefault(color, []).append(
                (required, str(card.get("name")), cost, untappedOnly)
            )
    allSources, untappedSources = _landSources(mainEntries, lookup)
    for color, entries in sorted(requirements.items()):
        entries.sort(key=lambda entry: (-entry[0], entry[1]))
        required, _, _, untappedOnly = entries[0]
        available = untappedSources[color] if untappedOnly else allSources[color]
        details = [
            f"{name} {cost} — {value}"
            for value, name, cost, _ in entries[:5]
        ]
        label = COLOR_NAMES.get(color, color)
        if available < required:
            findings.append(_finding(
                "warning",
                f"{label}: {available} / {required} land sources (short by {required - available}). "
                "Top demands:",
                SOURCE_SOURCES,
                SOURCE_SOURCES_LABEL,
            ) | {"details": details})
        else:
            findings.append(_finding(
                "info",
                f"{label}: {available} / {required} land sources.",
                SOURCE_SOURCES,
                SOURCE_SOURCES_LABEL,
            ) | {"details": details})

    tapped = 0
    for qty, cardId in mainEntries:
        card = lookup(cardId)
        if card is not None and "Land" in str(card.get("type_line", "")) and _isTappedLand(card):
            tapped += qty
    if tapped:
        findings.append(_finding(
            "info",
            f"Tapped lands: {tapped}. Turn-one requirements use untapped sources only.",
            SOURCE_SOURCES,
            SOURCE_SOURCES_LABEL,
        ))

    if oracletags.hasCache():
        coverage = {}
        for category, tags in TAG_CATEGORIES.items():
            names = []
            quantity = 0
            for qty, cardId in mainEntries:
                card = lookup(cardId)
                if card is None:
                    continue
                cardTags = set(oracletags.getCachedTags(card.get("oracle_id")))
                matches = bool(cardTags & (tags - {"counterspell-prefix", "tutor-prefix", "protects-prefix"}))
                if not matches and "counterspell-prefix" in tags:
                    matches = any(tag.startswith("counterspell") for tag in cardTags)
                if not matches and "tutor-prefix" in tags:
                    matches = any(tag.startswith("tutor-") for tag in cardTags)
                if not matches and "protects-prefix" in tags:
                    matches = any(tag.startswith("protects-") for tag in cardTags)
                if matches:
                    quantity += qty
                    names.append(str(card.get("name")))
            coverage[category] = (quantity, names)
        rows = []
        for category, (quantity, names) in coverage.items():
            if names:
                extra = f" +{len(names) - 3} more" if len(names) > 3 else ""
                cardText = ", ".join(names[:3]) + extra
            else:
                cardText = "—"
            rows.append({"category": category, "count": quantity, "cards": cardText})
        findings.append(_finding(
            "info",
            "Functional coverage from oracle tags:",
            SOURCE_TAGS,
            SOURCE_TAGS_LABEL,
        ) | {"coverage": rows})

    return findings


def commanderCurveTarget(deck: dict, cardLookup) -> list[int] | None:
    """Return Karsten's 1..6 drop curve target for the deck's commander."""
    if deck.get("format") != "commander":
        return None
    commanders = [cardLookup(entry[1]) for entry in _commanderCards(deck)]
    commanders = [card for card in commanders if card is not None]
    if len(commanders) != 1:
        return None
    mv = commanders[0].get("cmc")
    if mv is None:
        return None
    return CURVE_TARGETS.get(int(mv))
