import constants
from lib import scryfall


def getFormatInfo(formatKey: str) -> dict:
    return constants.DECK_FORMATS.get(formatKey, constants.DECK_FORMATS[constants.DEFAULT_DECK_FORMAT])


def allowedSections(formatKey: str) -> set[str]:
    info = getFormatInfo(formatKey)
    sections = {"main"}
    if info.get("sideboard"):
        sections.add("sideboard")
    if info.get("commander"):
        sections.add("commander")
    return sections


def _count(cards: list) -> int:
    return sum(int(card[0]) for card in cards)


def _isBasicLand(cardId: str) -> bool:
    card = scryfall.getCardById(cardId)
    return card is not None and "Basic Land" in card.get("type_line", "")


def validateDeck(deck: dict) -> list[str]:
    formatKey = deck.get("format", constants.DEFAULT_DECK_FORMAT)
    info = getFormatInfo(formatKey)
    main = deck.get("cardList") or []
    sideboard = deck.get("sideboard") or []
    commander = deck.get("commander") or []
    messages = []

    sideboardCount = _count(sideboard)
    commanderCount = _count(commander)
    mainCount = _count(main)

    if sideboardCount > 0 and not info.get("sideboard"):
        messages.append(f"Sideboard is not allowed in {info['label']}.")
    maxSideboard = info.get("maxSideboard")
    if maxSideboard is not None and sideboardCount > maxSideboard:
        messages.append(f"Sideboard has {sideboardCount} cards; maximum is {maxSideboard}.")

    if commanderCount > 0 and not info.get("commander"):
        messages.append(f"Commanders are not allowed in {info['label']}.")

    if info.get("commander"):
        commanderMin = info.get("commanderMin", 0)
        commanderMax = info.get("commanderMax", 0)
        if commanderCount < commanderMin:
            messages.append(f"Select at least {commanderMin} commander(s).")
        if commanderMax and commanderCount > commanderMax:
            messages.append(f"Too many commanders ({commanderCount}); maximum is {commanderMax}.")

    deckSize = info.get("deckSize")
    if deckSize is not None:
        total = mainCount + (commanderCount if info.get("commander") else 0)
        if info.get("commander"):
            if total != deckSize:
                messages.append(
                    f"Deck has {total} cards; {info['label']} decks need exactly {deckSize} including commanders."
                )
        elif total < deckSize:
            messages.append(f"Deck has {total} cards; minimum is {deckSize}.")

    if info.get("singleton"):
        counts = {}
        basicCache = {}
        for qty, cardId in main + commander:
            counts[cardId] = counts.get(cardId, 0) + int(qty)
        for cardId, qty in counts.items():
            if qty <= 1:
                continue
            if cardId not in basicCache:
                basicCache[cardId] = _isBasicLand(cardId)
            if not basicCache[cardId]:
                messages.append(f"Singleton rule: {qty} copies of the same card.")

    return messages
