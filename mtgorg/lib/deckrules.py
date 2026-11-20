import constants
from lib import scryfall


FOUR_OF_FORMATS = {"standard", "pioneer", "modern", "legacy", "pauper"}

COMMANDER_BRACKET_LABELS = {
    1: "Exhibition",
    2: "Core",
    3: "Upgraded",
    4: "Optimized",
    5: "cEDH",
}

MASS_LAND_DENIAL_CARDS = {
    "Armageddon",
    "Ruination",
    "Sunder",
    "Winter Orb",
    "Blood Moon",
    "Back to Basics",
    "Static Orb",
    "Stasis",
    "Rising Waters",
    "Tangle Wire",
    "Hokori, Dust Drinker",
    "Cataclysm",
    "Decree of Annihilation",
    "Jokulhaups",
    "Obliterate",
    "Devastation",
    "Wildfire",
    "Burning of Xinye",
    "Boom // Bust",
    "Impending Disaster",
    "Global Ruin",
    "Fall of the Thran",
    "Ravages of War",
}

KNOWN_TWO_CARD_COMBOS = [
    ("Thassa's Oracle", "Demonic Consultation"),
    ("Thassa's Oracle", "Tainted Pact"),
    ("Kiki-Jiki, Mirror Breaker", "Zealous Conscripts"),
    ("Kiki-Jiki, Mirror Breaker", "Restoration Angel"),
    ("Heliod, Sun-Crowned", "Walking Ballista"),
    ("Exquisite Blood", "Sanguine Bond"),
    ("Exquisite Blood", "Vito, Thorn of the Dusk Rose"),
    ("Niv-Mizzet, Parun", "Curiosity"),
    ("Niv-Mizzet, the Firemind", "Curiosity"),
    ("Isochron Scepter", "Dramatic Reversal"),
    ("Underworld Breach", "Brain Freeze"),
    ("Worldgorger Dragon", "Animate Dead"),
    ("Mikaeus, the Unhallowed", "Triskelion"),
    ("Godo, Bandit Warlord", "Helm of the Host"),
    ("Kinnan, Bonder Prodigy", "Basalt Monolith"),
    ("Food Chain", "Eternal Scourge"),
    ("Food Chain", "Misthollow Griffin"),
    ("Devoted Druid", "Vizier of Remedies"),
    ("Dockside Extortionist", "Temur Sabertooth"),
]

MASS_LAND_DENIAL_TEXT = (
    "destroy all lands",
    "destroy each land",
    "exile all lands",
    "exile each land",
    "return all lands",
    "return each land",
    "sacrifice all lands",
    "sacrifice each land",
    "lands don't untap",
    "lands do not untap",
    "tap all lands",
    "tap each land",
    "nonbasic lands are",
    "all lands become",
    "each land becomes",
)

LEGALITY_KEYS = {
    "standard": "standard",
    "pioneer": "pioneer",
    "modern": "modern",
    "legacy": "legacy",
    "vintage": "vintage",
    "pauper": "pauper",
    "commander": "commander",
    "brawl": "brawl",
    "historicbrawl": "historicbrawl",
    "oathbreaker": "oathbreaker",
}


def getFormatInfo(formatKey: str) -> dict:
    return constants.DECK_FORMATS.get(formatKey, constants.DECK_FORMATS[constants.DEFAULT_DECK_FORMAT])


def allowedSections(formatKey: str) -> set[str]:
    info = getFormatInfo(formatKey)
    sections = {"main"}
    if info.get("sideboard"):
        sections.add("sideboard")
    if info.get("commander"):
        sections.add("commander")
    if info.get("companion"):
        sections.add("companion")
    return sections


def _count(cards: list) -> int:
    return sum(int(card[0]) for card in cards)


def _cardKey(card: dict | None, cardId: str) -> str:
    if card is None:
        return cardId
    return card.get("oracle_id") or card.get("name") or cardId


def _isBasicLand(card: dict | None) -> bool:
    return card is not None and "Basic Land" in card.get("type_line", "")


def _allowsAnyNumber(card: dict | None) -> bool:
    if card is None:
        return False
    return "any number of cards named" in card.get("oracle_text", "").lower()


def _cardText(card: dict) -> str:
    return " ".join([
        card.get("oracle_text", ""),
        " ".join(card.get("keywords", [])),
    ]).lower()


def _validCommanderPair(first: dict, second: dict) -> bool:
    firstText = _cardText(first)
    secondText = _cardText(second)
    if "partner" in firstText and "partner" in secondText:
        return True
    if "friends forever" in firstText and "friends forever" in secondText:
        return True
    if "doctor's companion" in firstText and "doctor's companion" in secondText:
        return True
    firstIsBackground = "background" in first.get("type_line", "").lower()
    secondIsBackground = "background" in second.get("type_line", "").lower()
    if "choose a background" in firstText and secondIsBackground:
        return True
    if "choose a background" in secondText and firstIsBackground:
        return True
    return False


def _legalForFormat(card: dict, formatKey: str) -> str | None:
    legalityKey = LEGALITY_KEYS.get(formatKey)
    if legalityKey is None:
        return None
    legalities = card.get("legalities", {})
    if legalityKey not in legalities:
        return None
    return legalities[legalityKey]


def _summarize(names: list[str], limit: int = 5) -> str:
    shown = ", ".join(names[:limit])
    if len(names) > limit:
        shown += f", and {len(names) - limit} more"
    return shown


def _cardIssue(card: dict | None, cardId: str, status: str, reason: str) -> dict:
    return {
        "card": card.get("name", cardId) if card is not None else cardId,
        "status": status,
        "reason": reason,
    }


def analyzeCommanderBracket(deck: dict, cardCache: dict | None = None) -> dict | None:
    if deck.get("format", constants.DEFAULT_DECK_FORMAT) != "commander":
        return None
    cardCache = cardCache if cardCache is not None else {}
    for section in ("cardList", "sideboard", "commander", "companion"):
        for _qty, cardId in deck.get(section) or []:
            if cardId not in cardCache:
                cardCache[cardId] = scryfall.getCardById(cardId)
    cards = {cardId: cardCache.get(cardId) for section in ("cardList", "sideboard", "commander", "companion")
             for _qty, cardId in deck.get(section) or []}

    gameChangers = []
    extraTurns = []
    massLandDenial = []
    tutors = []
    infinite = []
    names = set()
    for card in cards.values():
        if card is not None:
            names.add(card.get("name", ""))
    possibleCombos = []
    for first, second in KNOWN_TWO_CARD_COMBOS:
        if first in names and second in names:
            possibleCombos.append(f"{first} + {second}")
    for card in cards.values():
        if card is None:
            continue
        name = card.get("name", "")
        text = _cardText(card)
        if card.get("game_changer"):
            gameChangers.append(name)
        if "extra turn" in text:
            extraTurns.append(name)
        if name in MASS_LAND_DENIAL_CARDS or any(pattern in text for pattern in MASS_LAND_DENIAL_TEXT):
            massLandDenial.append(name)
        if "search your library for" in text:
            tutors.append(name)
        if "infinite" in text:
            infinite.append(name)

    floor = 1
    if extraTurns:
        floor = max(floor, 2)
    if gameChangers:
        floor = max(floor, 3)
    if len(gameChangers) > 3 or massLandDenial:
        floor = max(floor, 4)
    if possibleCombos:
        floor = max(floor, 3)

    selected = deck.get("bracket")
    if selected is not None:
        selected = int(selected)
        if selected < 1 or selected > 5:
            selected = None

    issues = []
    if selected is not None:
        if selected < floor:
            issues.append(
                f"Bracket {selected} is below the suggested minimum Bracket {floor}."
            )
        if selected <= 2 and gameChangers:
            issues.append(f"Bracket {selected} does not allow Game Changers.")
        if selected <= 3 and massLandDenial:
            issues.append(f"Bracket {selected} does not allow mass land denial.")
        if selected == 1 and extraTurns:
            issues.append("Bracket 1 does not allow extra-turn cards.")
        if selected <= 2 and possibleCombos:
            issues.append("Bracket 1/2 does not allow intentional two-card combos.")
        if selected <= 3 and len(extraTurns) > 2:
            issues.append("Multiple extra-turn cards detected; verify there is no chaining/loop.")
        if selected <= 2 and len(tutors) > 5:
            issues.append(f"Bracket {selected} expects sparse tutors; {len(tutors)} detected.")

    guidance = [
        "Automatic estimate cannot determine intent, combo timing, tutor density, or cEDH mindset.",
    ]
    if possibleCombos:
        guidance.append("Review detected combos and whether they are early-game/cheap.")
    if selected == 3 and possibleCombos:
        issues.append("Possible two-card combos detected; Bracket 3 disallows early-game combos.")

    return {
        "floor": floor,
        "selected": selected,
        "issues": issues,
        "gameChangers": sorted(gameChangers),
        "extraTurns": sorted(extraTurns),
        "massLandDenial": sorted(massLandDenial),
        "tutors": sorted(tutors),
        "infinite": sorted(infinite),
        "possibleCombos": possibleCombos,
        "guidance": guidance,
    }


def validateDeckDetails(deck: dict, cardLookup=None) -> dict:
    cardLookup = cardLookup or scryfall.getCardById
    formatKey = deck.get("format", constants.DEFAULT_DECK_FORMAT)
    info = getFormatInfo(formatKey)
    main = deck.get("cardList") or []
    sideboard = deck.get("sideboard") or []
    commander = deck.get("commander") or []
    companion = deck.get("companion") or []
    issues = []
    cardIssues = []

    cardCache = {}

    def getCard(cardId: str) -> dict | None:
        if cardId not in cardCache:
            cardCache[cardId] = cardLookup(cardId)
        return cardCache[cardId]

    sideboardCount = _count(sideboard)
    commanderCount = _count(commander)
    companionCount = _count(companion)
    mainCount = _count(main)

    if companionCount > 1:
        issues.append("A deck can only have one companion.")
    for _qty, cardId in companion:
        card = getCard(cardId)
        if card is None:
            continue
        text = _cardText(card)
        if "companion" not in text:
            cardIssues.append(_cardIssue(
                card, cardId, "✗ companion", "Card does not have the companion ability"
            ))
            issues.append(f"{card.get('name', cardId)} is not a companion card.")

    if sideboardCount > 0 and not info.get("sideboard"):
        issues.append(f"Sideboard is not allowed in {info['label']}.")
    maxSideboard = info.get("maxSideboard")
    if maxSideboard is not None and sideboardCount > maxSideboard:
        issues.append(f"Sideboard has {sideboardCount} cards; maximum is {maxSideboard}.")

    if commanderCount > 0 and not info.get("commander"):
        issues.append(f"Commanders are not allowed in {info['label']}.")

    if info.get("commander"):
        commanderMin = info.get("commanderMin", 0)
        commanderMax = info.get("commanderMax", 0)
        if commanderCount < commanderMin:
            issues.append(f"Select at least {commanderMin} commander(s).")
        if commanderMax and commanderCount > commanderMax:
            issues.append(f"Too many commanders ({commanderCount}); maximum is {commanderMax}.")
        elif commanderCount == 2 and formatKey in ("commander", "brawl", "historicbrawl"):
            commanderCards = [getCard(cardId) for qty, cardId in commander for _ in range(int(qty))]
            if all(card is not None for card in commanderCards):
                if not _validCommanderPair(commanderCards[0], commanderCards[1]):
                    issues.append("The two commanders are not a valid partner/background pair.")

    deckSize = info.get("deckSize")
    if deckSize is not None:
        total = mainCount + (commanderCount if info.get("commander") else 0)
        if info.get("commander"):
            if total != deckSize:
                issues.append(
                    f"Deck has {total} cards; {info['label']} decks need exactly {deckSize} including commanders."
                )
        elif total < deckSize:
            issues.append(f"Deck has {total} cards; minimum is {deckSize}.")

    if info.get("commander") and formatKey in ("commander", "brawl", "historicbrawl"):
        commanderCards = [getCard(cardId) for qty, cardId in commander for _ in range(int(qty))]
        if commanderCards and all(card is not None for card in commanderCards):
            colorIdentity = set()
            for card in commanderCards:
                colorIdentity.update(card.get("color_identity", []))
            outside = []
            for _qty, cardId in main + commander + companion:
                card = getCard(cardId)
                if card is None:
                    continue
                extraColors = set(card.get("color_identity", [])) - colorIdentity
                if extraColors:
                    outside.append(card.get("name", cardId))
                    cardIssues.append(_cardIssue(
                        card,
                        cardId,
                        "✗ identity",
                        f"{''.join(sorted(extraColors))} not in commander identity "
                        f"{''.join(sorted(colorIdentity))}",
                    ))
            if outside:
                issues.append(f"Cards outside commander colour identity: {_summarize(outside)}.")

    legalityKey = LEGALITY_KEYS.get(formatKey)
    if legalityKey is not None:
        illegal = []
        for _qty, cardId in main + sideboard + commander + companion:
            card = getCard(cardId)
            if card is None:
                continue
            legality = _legalForFormat(card, formatKey)
            if legality is not None and legality not in ("legal", "restricted"):
                illegal.append(f"{card.get('name', cardId)} ({legality})")
                cardIssues.append(_cardIssue(
                    card,
                    cardId,
                    "✗ legality",
                    f"{legality} in {info['label']}",
                ))
        if illegal:
            issues.append(f"Not legal in {info['label']}: {_summarize(illegal)}.")

    if info.get("singleton"):
        counts = {}
        basics = {}
        anyNumber = {}
        for qty, cardId in main + commander:
            card = getCard(cardId)
            key = _cardKey(card, cardId)
            counts[key] = counts.get(key, 0) + int(qty)
            if card is not None:
                basics[key] = _isBasicLand(card)
                anyNumber[key] = _allowsAnyNumber(card)
        for key, qty in counts.items():
            if qty <= 1 or basics.get(key) or anyNumber.get(key):
                continue
            card = getCard(next(
                (cardId for _qty, cardId in main + commander
                 if _cardKey(getCard(cardId), cardId) == key),
                "",
            ))
            cardIssues.append(_cardIssue(
                card,
                key,
                "✗ singleton",
                f"{qty} copies (max 1)",
            ))

    if formatKey in FOUR_OF_FORMATS:
        counts = {}
        basics = {}
        anyNumber = {}
        for qty, cardId in main + sideboard:
            card = getCard(cardId)
            key = _cardKey(card, cardId)
            counts[key] = counts.get(key, 0) + int(qty)
            if card is not None:
                basics[key] = _isBasicLand(card)
                anyNumber[key] = _allowsAnyNumber(card)
        for key, qty in counts.items():
            if qty <= 4 or basics.get(key) or anyNumber.get(key):
                continue
            card = getCard(next(
                (cardId for _qty, cardId in main + sideboard
                 if _cardKey(getCard(cardId), cardId) == key),
                "",
            ))
            cardIssues.append(_cardIssue(
                card,
                key,
                "✗ copies",
                f"{qty} copies (max 4)",
            ))

    bracket = analyzeCommanderBracket(deck, cardCache)
    if bracket is not None:
        issues.extend(bracket["issues"])
        cardByName = {}
        for _qty, cardId in main + sideboard + commander + companion:
            card = getCard(cardId)
            if card is not None:
                cardByName[card.get("name", cardId)] = (cardId, card)
        selected = bracket.get("selected")

        def addBracketCard(name: str, status: str, reason: str):
            cardId, card = cardByName.get(name, (name, None))
            cardIssues.append(_cardIssue(card, cardId, status, reason))

        if selected is not None:
            if selected <= 2:
                for name in bracket["gameChangers"]:
                    addBracketCard(name, "✗ game changer", f"Not allowed in Bracket {selected}")
            if selected <= 3:
                for name in bracket["massLandDenial"]:
                    addBracketCard(name, "✗ land denial", f"Not allowed in Bracket {selected}")
            if selected == 1:
                for name in bracket["extraTurns"]:
                    addBracketCard(name, "✗ extra turn", "Not allowed in Bracket 1")
            if selected <= 3 and len(bracket["extraTurns"]) > 2:
                for name in bracket["extraTurns"]:
                    addBracketCard(name, "✗ extra turns", "Multiple extra turns risk chaining/loops")
            if selected <= 2:
                for combo in bracket["possibleCombos"]:
                    first, _, second = combo.partition(" + ")
                    addBracketCard(first, "✗ combo", f"Possible combo with {second}")
                    addBracketCard(second, "✗ combo", f"Possible combo with {first}")
                if len(bracket["tutors"]) > 5:
                    for name in bracket["tutors"]:
                        addBracketCard(
                            name, "✗ tutor density",
                            f"Bracket {selected} expects sparse tutors ({len(bracket['tutors'])} detected)",
                        )

    return {
        "format": formatKey,
        "label": info["label"],
        "issues": issues,
        "cards": cardIssues,
        "bracket": bracket,
    }


def validateDeck(deck: dict) -> list[str]:
    details = validateDeckDetails(deck)
    messages = list(details["issues"])
    return messages
