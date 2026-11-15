import datetime
import logging
import re
from pathlib import Path
from fuzzywuzzy import fuzz, process
import aiohttp
import requests
import os

import scrython.cards
import scrython.sets
from scrython.base import ScryfallError, ScrythonRequestHandler

import connector
from lib import bulk, utils
import constants

# Register a custom Scryfall User-Agent whenever this module is imported.
ScrythonRequestHandler.set_user_agent(
    "MTGOrganizer/1.0 (https://github.com/justinbacle/mtg-org)"
)

_sets_memory_cache: list | None = None
_bulkSetsCache: list | None = None
_formats_memory_cache: list | None = None
_failedSetIcons: set[str] = set()

SEARCH_DICT_KEYS = [
    'order',
    'unique',
    'dir',
    'include_variations',
    'include_extras',
    'include_multilingual',
    'page',
]


class Card(dict):
    def __init__(self, dataDict):
        super().__init__(dataDict)


def resetBulkDataCache():
    global _bulkSetsCache
    bulk.resetBulkCaches()
    _bulkSetsCache = None


def resetSetsCache():
    global _sets_memory_cache, _bulkSetsCache, _failedSetIcons
    _sets_memory_cache = None
    _bulkSetsCache = None
    _failedSetIcons = set()


def resetSetIconCache():
    global _failedSetIcons
    _failedSetIcons = set()


def resetFormatsCache():
    global _formats_memory_cache
    _formats_memory_cache = None


def _getBulkCache() -> bulk.BulkCache:
    return bulk.getBulkCache()


def getBulkCardCount() -> int:
    return _getBulkCache().count()


def ensureBulkDataReady(progress_callback=None) -> int:
    cache = _getBulkCache()
    cache.ensureReady(progress_callback=progress_callback)
    return cache.count()


def _getLocalPrintings(card: dict) -> list:
    oracleId = card.get("oracle_id")
    if oracleId is None:
        return []
    return _getBulkCache().getCardsByOracleId(oracleId)


def _matchesColorFilter(card: dict, colorFilter: str) -> bool:
    requested = re.findall(r"(?<!-)\bc:([wubrg]+)", colorFilter)
    excluded = re.findall(r"-c:([wubrg]+)", colorFilter)
    cardColors = {color.lower() for color in card.get("colors", [])}
    for group in requested:
        if not set(group) <= cardColors:
            return False
    for group in excluded:
        if cardColors & set(group):
            return False
    return True


def _parseComparator(value) -> tuple[str, float] | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*(<=|>=|=|<|>)\s*(-?\d+(?:\.\d+)?)\s*", str(value))
    if match is None:
        return None
    return match.group(1), float(match.group(2))


def _compareNumber(value, comparator: tuple[str, float]) -> bool:
    if value in (None, "", "*"):
        return False
    try:
        number = float(str(value))
    except ValueError:
        return False
    operator, target = comparator
    if operator == "<":
        return number < target
    if operator == "<=":
        return number <= target
    if operator == ">":
        return number > target
    if operator == ">=":
        return number >= target
    return number == target


def _cardOracleText(card: dict) -> str:
    if "oracle_text" in card:
        return card.get("oracle_text", "")
    return " ".join(face.get("oracle_text", "") for face in card.get("card_faces", []))


def _filterCards(cards: list, searchDict: dict) -> list:
    setCode = searchDict.get("set") or searchDict.get("in")
    lang = searchDict.get("lang")
    rarity = searchDict.get("rarity")
    colorFilter = searchDict.get("colors")
    types = [cardType.lower() for cardType in searchDict.get("types", []) if cardType]
    oracle = searchDict.get("oracle", "")
    cmcFilter = searchDict.get("cmc")
    cmcComparator = None
    if isinstance(cmcFilter, (list, tuple)) and len(cmcFilter) >= 2 and str(cmcFilter[1]).strip() != "":
        cmcComparator = _parseComparator(f"{cmcFilter[0]}{cmcFilter[1]}")
    elif isinstance(cmcFilter, str):
        cmcComparator = _parseComparator(cmcFilter)
    powerComparator = _parseComparator(searchDict.get("pow"))
    toughnessComparator = _parseComparator(searchDict.get("tou"))
    loyaltyComparator = _parseComparator(searchDict.get("loy"))
    formatName = searchDict.get("f")
    game = searchDict.get("game")
    priceFilter = searchDict.get("price")

    filtered = []
    for card in cards:
        if setCode and card.get("set", "").lower() != setCode.lower():
            continue
        if lang not in (None, "", "any") and card.get("lang", "en") != lang:
            continue
        if rarity and card.get("rarity") != rarity:
            continue
        if colorFilter and not _matchesColorFilter(card, colorFilter):
            continue
        typeLine = card.get("type_line", "").lower()
        if any(cardType not in typeLine for cardType in types):
            continue
        if oracle and oracle.lower() not in _cardOracleText(card).lower():
            continue
        if cmcComparator is not None and not _compareNumber(card.get("cmc"), cmcComparator):
            continue
        if powerComparator is not None and not _compareNumber(card.get("power"), powerComparator):
            continue
        if toughnessComparator is not None and not _compareNumber(card.get("toughness"), toughnessComparator):
            continue
        if loyaltyComparator is not None and not _compareNumber(card.get("loyalty"), loyaltyComparator):
            continue
        if formatName and card.get("legalities", {}).get(formatName, "").lower() != "legal":
            continue
        if game == "paper" and "paper" not in card.get("games", []):
            continue
        if priceFilter:
            match = re.fullmatch(r"(eur|usd|tix)(<=|>=|=|<|>)(\d+(?:\.\d+)?)", str(priceFilter))
            if match is not None:
                currency, operator, target = match.groups()
                price = card.get("prices", {}).get(currency)
                if not _compareNumber(price, (operator, float(target))):
                    continue
        filtered.append(card)
    return filtered


def _copyBulkCard(card: dict) -> Card:
    return Card(dict(card))


SUPPLEMENTAL_SET_CODES = {"plst", "spg", "ulst"}

SET_TYPE_RANK = {
    "core": 0,
    "expansion": 0,
    "masters": 0,
    "commander": 0,
    "draft_innovation": 0,
    "starter": 1,
    "duel_deck": 1,
    "archenemy": 1,
    "planechase": 1,
    "box": 2,
    "arsenal": 2,
    "from_the_vault": 2,
    "premium_deck": 2,
    "spellbook": 2,
    "treasure_chest": 2,
    "masterpiece": 2,
    "eternal": 2,
    "promo": 3,
    "alchemy": 3,
    "funny": 3,
    "memorabilia": 4,
    "token": 5,
    "vanguard": 5,
    "minigame": 5,
}


def _collectorSortKey(card: dict) -> int:
    numbers = re.findall(r"\d+", str(card.get("collector_number", "")))
    return int(numbers[-1]) if numbers else 999999


def _printingPreference(card: dict) -> tuple:
    """Prefer common booster printings, then regular nonfoil variants."""
    frameEffects = set(card.get("frame_effects") or [])
    specialFrame = bool(frameEffects - {"legendary"})
    isPromo = bool(card.get("promo_types")) or bool(card.get("promo"))
    finishes = card.get("finishes") or []
    hasNonfoil = "nonfoil" in finishes
    prices = card.get("prices") or {}
    hasNonfoilPrice = prices.get(constants.CURRENCY[0]) is not None
    setRank = SET_TYPE_RANK.get(card.get("set_type"), 3)
    if card.get("set") in SUPPLEMENTAL_SET_CODES:
        setRank = 3
    return (
        0 if card.get("booster") else 1,
        setRank,
        isPromo,
        specialFrame,
        not hasNonfoil,
        not hasNonfoilPrice,
    )


def _sortPrintings(cards: list) -> list:
    cards = sorted(cards, key=_collectorSortKey)
    cards = sorted(cards, key=lambda card: card.get("released_at", ""), reverse=True)
    return sorted(cards, key=_printingPreference)


def _dedupeByOracle(cards: list) -> list:
    seen = set()
    deduped = []
    for card in cards:
        key = card.get("oracle_id") or card.get("id")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(card)
    return deduped


def searchCards(searchDict: dict, exact: bool = False):
    if constants.USE_BULK_FILES:
        if searchDict.get("atag") or searchDict.get("otag"):
            logging.info("Art/oracle tags are not in bulk data; using online Scryfall search")
            return searchCardsOnline(searchDict, exact)
        return searchCardsLocal(searchDict, exact)
    return searchCardsOnline(searchDict, exact)


def _searchCardsLocalNoName(searchDict: dict, limit: int) -> tuple[list, bool]:
    cache = _getBulkCache()
    cards = _filterCards(cache.iterCardsFiltered(searchDict, limit=limit + 1), searchDict)
    truncated = len(cards) > limit
    cards = _sortPrintings(cards)
    cards = _dedupeByOracle(cards)
    return [_copyBulkCard(card) for card in cards[:limit]], truncated


def searchCardsLimited(searchDict: dict, limit: int, exact: bool = False):
    if constants.USE_BULK_FILES and not (searchDict.get("atag") or searchDict.get("otag")):
        if not searchDict.get("name"):
            return _searchCardsLocalNoName(searchDict, limit)
        cards = searchCardsLocal(searchDict, exact, limit=limit + 1)
    else:
        cards = searchCards(searchDict, exact)
    truncated = len(cards) > limit
    return cards[:limit], truncated


def searchCardsLocal(searchDict: dict, exact: bool = False, limit: int | None = None):
    cache = _getBulkCache()
    name = searchDict.get("name", "")
    if exact and name:
        cards = cache.getCardsByName(name)
        cards = _filterCards(cards, searchDict)
        cards = _sortPrintings(cards)
        return [_copyBulkCard(card) for card in cards]

    if name:
        needle = name.lower()
        fuzzyScores = None
        candidates = cache.searchNameSubstring(needle)
        if not candidates:
            fuzzyScores = {}
            fuzzyMatches = process.extractBests(
                needle,
                cache.getDistinctNames(),
                scorer=fuzz.WRatio,
                score_cutoff=80,
                limit=20,
            )
            for matchedName, score in fuzzyMatches:
                fuzzyScores[matchedName] = score
                candidates.extend(cache.getCardsByName(matchedName))
        candidates = _filterCards(candidates, searchDict)
        candidates = _sortPrintings(candidates)
        if fuzzyScores is not None:
            candidates.sort(
                key=lambda card: fuzzyScores.get(card.get("name", "").lower(), 0),
                reverse=True,
            )
        else:
            candidates.sort(
                key=lambda card: (
                    card.get("name", "").lower().find(needle),
                    len(card.get("name", "")),
                )
            )
        candidates = _dedupeByOracle(candidates)
        return [_copyBulkCard(card) for card in candidates]

    cards = _filterCards(cache.iterCardsFiltered(searchDict, limit=limit), searchDict)
    cards = _sortPrintings(cards)
    cards = _dedupeByOracle(cards)
    return [_copyBulkCard(card) for card in cards]


def searchCardsOnline(searchDict: dict, exact: bool = False):
    cards = []
    kwargs = {}
    if "lang" not in searchDict.keys():
        searchDict.update({"lang": "any"})
    q = ""
    for k, v in searchDict.items():
        if k in SEARCH_DICT_KEYS:
            kwargs.update({k: v})
        elif k == "name":
            if v != "":
                if exact:  # https://scryfall.com/docs/syntax#exact
                    q += "!\"" + v + "\" "
                else:
                    q += "\"" + v + "\" "
        elif k in ["colors", "price"]:
            if v is not None:  # already comes formatted correctly
                q += v + " "
        elif k in ["pow", "tou", "loy"]:
            q += k + v + " "
        elif k == "types":
            for type in v:
                if type != "":
                    q += "t:" + type + " "
        elif k == "oracle":
            if v != "":
                q += k + ":\"" + v + "\" "
        elif k == "atag":
            if v != "":
                q += "art:" + v + " "
        elif k == "cmc":
            if v[1] != "":
                q += "mv" + v[0] + v[1] + " "
        else:
            if v != "":
                q += k + ":" + v + " "
    try:
        scryfallReq = scrython.cards.Search(q=q, **kwargs)
    except (ScryfallError, aiohttp.ClientConnectorError) as e:
        # TODO display error msg, not connected to internet (suggest using bulk file)
        logging.warning(e)
    else:
        for card in scryfallReq.data:
            cards.append(Card(card.to_dict()))
        # When multiple printings match an exact name, always return the same
        # deterministic order. Prefer the most recently released printing so the
        # result is stable and predictable. Python's sort is stable, so printings
        # released on the same day keep Scryfall's original order.
        if exact and cards:
            cards = _sortPrintings(cards)
    return cards


def getCardPrintings(cardId: str) -> list:
    card = getCardById(cardId)
    if card is None:
        return []
    if constants.USE_BULK_FILES:
        printings = _getLocalPrintings(card)
    else:
        printings = _getPrintsSearchData(card)
    if not printings:
        return [Card(dict(card))]
    printings = _sortPrintings(printings)
    if cardId not in [printing.get("id") for printing in printings]:
        printings.insert(0, card)
    return [Card(dict(printing)) for printing in printings]


def getCardReprints(cardId: str):
    card = getCardById(cardId)
    if card is None:
        return []
    modeKey = bulk.BulkDataManager.getActiveBulkType() if constants.USE_BULK_FILES else "online"
    if "sets" in card.keys() and card.get("sets_mode") == modeKey:
        return card["sets"]
    if constants.USE_BULK_FILES:
        allPrintings = _getLocalPrintings(card)
    else:
        allPrintings = _getPrintsSearchData(card)
    if not allPrintings:
        return []
    sets = sorted({printing["set"] for printing in allPrintings if "set" in printing})
    connector.updateCard(cardId, {"sets": sets, "sets_mode": modeKey})
    return sets


def _getPrintsSearchData(card: dict) -> list:
    """Fetch all printings from a card's prints_search_uri, returning the data list."""
    printsUri = card.get("prints_search_uri")
    if printsUri is None:
        logging.warning(f"No prints_search_uri for card {card.get('id')}")
        return []
    reprintsDict = utils.getUrlJsonData(printsUri)
    if reprintsDict is None or "data" not in reprintsDict:
        logging.warning(
            f"prints_search_uri returned no data for card {card.get('id')}: {reprintsDict}"
        )
        return []
    allData = reprintsDict["data"]
    while reprintsDict.get("has_more") and "next_page" in reprintsDict:
        reprintsDict = utils.getUrlJsonData(reprintsDict["next_page"])
        if reprintsDict is None or "data" not in reprintsDict:
            logging.warning("Pagination request returned no data")
            break
        allData.extend(reprintsDict["data"])
    return allData


def _getCardReprintIdOnline(card: dict, setCode: str, lang: str = "en") -> list:
    allPrintings = _sortPrintings(_getPrintsSearchData(card))
    ids = [_card["id"] for _card in allPrintings if _card.get("set") == setCode]
    returnIdsList = []
    for id in ids:
        if lang != "en":
            try:
                _cardById = getCardById(id)
                if _cardById is None:
                    returnIdsList.append(id)
                    continue
                foundCard = scrython.cards.ByCodeNumber(
                    code=setCode, number=_cardById["collector_number"], lang=lang).to_dict()
                returnIdsList.append(foundCard["id"])
            except ScryfallError:
                logging.warning(f"Could not find {lang=} translation for given set")
                returnIdsList.append(id)
        else:
            returnIdsList.append(id)

    return returnIdsList


def getCardReprintId(cardId: str, setCode: str, lang: str = "en") -> list:
    # TODO add cache ?
    card = getCardById(cardId)
    if card is None:
        return []
    if constants.USE_BULK_FILES:
        allPrintings = _sortPrintings(_getLocalPrintings(card))
        localIds = [
            printing["id"] for printing in allPrintings
            if printing.get("set", "").lower() == setCode.lower()
            and printing.get("lang", "en") == lang
        ]
        if localIds or lang == "en":
            return localIds
    return _getCardReprintIdOnline(card, setCode, lang)


def _fetchCardById(id: str) -> dict | None:
    if constants.USE_BULK_FILES:
        card = _getBulkCache().getCardById(id)
        return _copyBulkCard(card) if card is not None else None
    try:
        scryfallReq = scrython.cards.ById(id=id)
    except ScryfallError:
        logging.error(f"Could not find card for {id=}")
        return None
    return Card(scryfallReq.to_dict())


def getCardById(id: str, force: bool = False):
    card = connector.getCard(id)
    if isinstance(card, dict) and "data" in card:
        card = card["data"]
    elif card is not None:
        logging.warning(f"Malformed cache entry for {id=}, refetching")
        card = None
    if force or card is None:
        card = _fetchCardById(id)
        if card is not None:
            connector.saveCard(id, card)
    return card


def getCardByMTGOId(mtgoId: int) -> dict | None:
    if constants.USE_BULK_FILES:
        cardData = _getBulkCache().getCardByMTGOId(mtgoId)
        if cardData is None:
            logging.warning(f"Could not find card for {mtgoId=}")
            return None
        return _copyBulkCard(cardData)
    url = f"https://api.scryfall.com/cards/mtgo/{mtgoId}"
    cardData = utils.getUrlJsonData(url)
    if cardData is None or cardData.get("object") == "error":
        logging.warning(f"Could not find card for {mtgoId=}")
        return None
    return cardData


def getRandomCard() -> dict:
    if constants.USE_BULK_FILES:
        card = _getBulkCache().getRandomCard()
        if card is None:
            raise RuntimeError("No cards available in bulk data")
        return _copyBulkCard(card)
    return scrython.cards.Random().to_dict()


def getSetData(setId, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["id"] == setId]
    if len(possibleSets) == 1:
        return possibleSets[0].get(dataKey)
    else:
        logging.error("Set ID could not be found. Maybe set cache is not up to date. Updating...")
        allSets = getSets(force=True)
        possibleSets = [_ for _ in allSets if _["id"] == setId]
        if len(possibleSets) == 1:
            return possibleSets[0].get(dataKey)
        else:
            logging.error(f"Could not find set for {setId=}")
            return None


def getSetDataByCode(setCode, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["code"] == setCode]
    if len(possibleSets) == 1:
        return possibleSets[0].get(dataKey)
    else:
        logging.error("Set code could not be found. Maybe set cache is not up to date. Updating...")
        allSets = getSets(force=True)
        possibleSets = [_ for _ in allSets if _["code"] == setCode]
        if len(possibleSets) == 1:
            return possibleSets[0].get(dataKey)
        else:
            logging.error(f"Could not find set for {setCode=}")
            return None


def getSetSymbol(setId):
    return getSetData(setId, "icon_svg_uri")


def _getSetIconUri(setId) -> str | None:
    symbolUri = getSetSymbol(setId)
    if symbolUri is not None:
        return symbolUri
    setCode = getSetData(setId, "code")
    if setCode is None:
        return None
    setData = utils.getUrlJsonData(f"https://api.scryfall.com/sets/{setCode}")
    if setData is not None and setData.get("icon_svg_uri") is not None:
        return setData["icon_svg_uri"]
    return f"https://svgs.scryfall.io/sets/{setCode}.svg"


def getSetSvg(setId):
    setIconFilePath = constants.DEFAULT_SET_ICONS_LOCATION / f"{setId}.svg"
    if setIconFilePath.is_file() and os.access(setIconFilePath, os.R_OK):
        return setIconFilePath.as_posix()
    if setId in _failedSetIcons:
        return None

    symbolUri = _getSetIconUri(setId)
    if symbolUri is None:
        _failedSetIcons.add(setId)
        return None
    svgData = utils.getUrlData(symbolUri, logErrors=False)
    if svgData is None:
        _failedSetIcons.add(setId)
        logging.warning(f"Could not download set icon for {setId} ({symbolUri})")
        return None
    with open(setIconFilePath, "w") as file:
        file.write(svgData)
    return setIconFilePath.as_posix()


def getSetReleaseYear(setId):
    releaseDate = getSetData(setId, "released_at")
    return None if releaseDate is None else releaseDate.split("-")[0]


def getOnlineSetData():
    setsData = {
        "_date": datetime.datetime.now().strftime(constants.TIME_FORMAT_STR),
        "sets": [s._scryfall_data for s in scrython.sets.All().data]
    }
    return setsData


def _getSetsFromBulk() -> list:
    global _bulkSetsCache
    if _bulkSetsCache is None:
        _bulkSetsCache = _getBulkCache().getSets()
    return _bulkSetsCache


def getSets(force: bool = False) -> list:
    if constants.USE_BULK_FILES:
        return _getSetsFromBulk()
    global _sets_memory_cache
    if not force and _sets_memory_cache is not None:
        return _sets_memory_cache
    setsJsonPath = Path(constants.DEFAULT_INFOS_LOCATION) / "sets.json"
    setsData = None
    if force or not setsJsonPath.is_file():
        setsData = getOnlineSetData()
        utils.saveJson(setsData, setsJsonPath)
    else:
        setsData = utils.loadJson(setsJsonPath)
    if setsJsonPath.is_file() and setsData is not None:
        savedTime = datetime.datetime.strptime(setsData["_date"], constants.TIME_FORMAT_STR)
        if datetime.datetime.now() - savedTime > datetime.timedelta(days=29):
            logging.warning("Sets data are a month old, trying to update")
            try:
                setsData = getOnlineSetData()
            except Exception as e:
                logging.error(e)
            else:
                utils.saveJson(setsData, setsJsonPath)
        else:
            if setsData is not None:
                setsData = utils.loadJson(setsJsonPath)
    if setsData is None:
        return []
    _sets_memory_cache = setsData["sets"]
    assert _sets_memory_cache is not None
    return _sets_memory_cache


def getSetByCode(setCode: str) -> dict | None:
    """Return the full set record for a given set code, or None if not found."""
    allSets = getSets()
    matches = [s for s in allSets if s["code"] == setCode]
    if matches:
        return matches[0]
    # Try refreshing once
    allSets = getSets(force=True)
    matches = [s for s in allSets if s["code"] == setCode]
    return matches[0] if matches else None


def downloadBulkData(bulkType: str | None = None, progress_callback=None) -> Path:
    return bulk.BulkDataManager(bulkType=bulkType).downloadBulkData(progress_callback=progress_callback)


def getTaggerTags():
    url = "https://scryfall.com/docs/tagger-tags"
    text = requests.get(url).text
    textLines = text.split("\n")
    isFunctionnal = False
    atags = []
    otags = []
    isAfterHeader = False
    for textLine in textLines:
        if re.match(r".*<h2>.*</h2>.*", textLine):
            isFunctionnal = "functional" in textLine
            isAfterHeader = True
        elif isAfterHeader and re.match(r".*<a href=\"/search\?.*>(.*)<.a>.*", textLine):
            # '<a href="/search?q=art%3Ainkwell&amp;unique=art">inkwell</a>'
            m = re.match(r".*<a href=\"/search\?.*>(.*)<.a>.*", textLine)
            assert m is not None
            tag = m.groups()[0]
            if isFunctionnal:
                otags.append(tag)
            else:
                atags.append(tag)
    return atags, otags


def getFormats() -> list:
    global _formats_memory_cache
    if _formats_memory_cache is not None:
        return _formats_memory_cache
    if constants.USE_BULK_FILES:
        card = _getBulkCache().getAnyCard()
        if card is not None:
            _formats_memory_cache = list(card.get("legalities", {}).keys())
            return _formats_memory_cache
    card = getRandomCard()
    _formats_memory_cache = list(card.get("legalities", {}).keys())
    return _formats_memory_cache
