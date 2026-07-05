import datetime
import logging
import json
from pathlib import Path
from cache_to_disk import cache_to_disk
from tqdm import tqdm
from fuzzywuzzy import fuzz  # install python-Levenshtein for faster results  # noqa F401
import aiohttp
import requests
import re
import os

import scrython.cards
import scrython.sets
from scrython.base import ScryfallError, ScrythonRequestHandler

import connector
from lib import utils
import constants

# Register a custom Scryfall User-Agent whenever this module is imported.
ScrythonRequestHandler.set_user_agent(
    "MTGOrganizer/1.0 (https://github.com/justinmtg/mtg-org)"
)

_sets_memory_cache: list | None = None


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


def searchCards(searchDict: dict, exact: bool = False):
    if constants.USE_BULK_FILES:
        return searchCardsLocal(searchDict, exact)
    else:
        return searchCardsOnline(searchDict, exact)


def searchCardsLocal(searchDict: dict, exact: bool = False):
    if exact:
        cards = list(filter(lambda x: x["name"].lower() == searchDict["name"].lower(), getBulkData()))
        return cards
    else:
        logging.error("not implemented yet using bulk data, only looking for close names")
        cards = []
        _bulkData = getBulkData()
        for id, name in tqdm([(_["id"], _["name"]) for _ in _bulkData]):
            if searchDict["name"].lower() in name.lower():
                cards.append(getCardById(id))
            # ? Fuzzy search too long ?
            # if fuzz.ratio(searchDict["name"], name) >= 60:
            #     cards.append(getCardById(id))
        return cards


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
            cards.sort(
                key=lambda c: c.get("released_at", ""),
                reverse=True,
            )
    return cards


def getCardReprints(cardId: str):
    card = getCardById(cardId)
    if card is None:
        return []
    if "sets" not in card.keys():  # Cache
        reprintsDict = utils.getUrlJsonData(card["prints_search_uri"])
        sets = [_["set"] for _ in reprintsDict["data"]]
        while reprintsDict["has_more"]:
            reprintsDict = utils.getUrlJsonData(reprintsDict["next_page"])
            sets += [_["set"] for _ in reprintsDict["data"]]
        sets = list(set(sets))
        connector.updateCard(cardId, {"sets": sets})
    else:
        sets = card["sets"]
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


def getCardReprintId(cardId: str, setCode: str, lang: str = "en") -> list:
    # TODO add cache ?
    card = getCardById(cardId)
    if card is None:
        return []
    allPrintings = _getPrintsSearchData(card)
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


def getCardById(id: str, force: bool = False):
    card = connector.getCard(id)
    if force or card is None:  # card not in Cache
        if constants.USE_BULK_FILES:
            card = list(filter(lambda x: x["id"] == id, getBulkData()))[0]
        else:
            try:
                scryfallReq = scrython.cards.ById(id=id)
            except ScryfallError:
                logging.error(f"Could not find card for {id=}")
                card = None
            else:
                card = Card(scryfallReq.to_dict())
        if card is not None:
            connector.saveCard(id, card)
    elif isinstance(card, dict) and "data" in card:
        card = card["data"]
    else:
        logging.warning(f"Malformed cache entry for {id=}, refetching")
        card = None
        try:
            scryfallReq = scrython.cards.ById(id=id)
        except ScryfallError:
            logging.error(f"Could not find card for {id=}")
        else:
            card = Card(scryfallReq.to_dict())
            connector.saveCard(id, card)
    return card


def getCardByMTGOId(mtgoId: int) -> dict:
    if constants.USE_BULK_FILES:
        cardData = list(filter(lambda x: x["mtgo_id"] == mtgoId, getBulkData()))[0]
    else:
        url = f"https://api.scryfall.com/cards/mtgo/{mtgoId}"
        cardData = utils.getUrlJsonData(url)
    return cardData


def getRandomCard() -> dict:
    return scrython.cards.Random().to_dict()


def getSetData(setId, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["id"] == setId]
    if len(possibleSets) == 1:
        return possibleSets[0][dataKey]
    else:
        logging.error("Set ID could not be found. Maybe set cache is not up to date. Updating...")
        allSets = getSets(force=True)
        possibleSets = [_ for _ in allSets if _["id"] == setId]
        if len(possibleSets) == 1:
            return possibleSets[0][dataKey]
        else:
            logging.error(f"Could not find set for {setId=}")
            return None


def getSetDataByCode(setCode, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["code"] == setCode]
    if len(possibleSets) == 1:
        return possibleSets[0][dataKey]
    else:
        logging.error("Set code could not be found. Maybe set cache is not up to date. Updating...")
        allSets = getSets(force=True)
        possibleSets = [_ for _ in allSets if _["code"] == setCode]
        if len(possibleSets) == 1:
            return possibleSets[0][dataKey]
        else:
            logging.error(f"Could not find set for {setCode=}")
            return None


def getSetSymbol(setId):
    return getSetData(setId, "icon_svg_uri")


def getSetSvg(setId):
    setIconFilePath = constants.DEFAULT_SET_ICONS_LOCATION / f"{setId}.svg"
    if not (setIconFilePath.is_file() and os.access(setIconFilePath, os.R_OK)):
        if constants.USE_BULK_FILES:  # TODO preload set icons ?
            logging.error(f"Missing local data for {setId=}")
        else:
            svgData = utils.getUrlData(getSetSymbol(setId))
            if svgData is not None:
                f = open(setIconFilePath, 'w')
                f.write(svgData)
                f.close()
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


# @cache_to_disk(1)
def getSets(force: bool = False) -> list:
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


@cache_to_disk(1)
def getBulkData():  # TODO load into a tinyDB object ?
    bulkFiles = os.listdir(constants.DEFAULT_BULK_FOLDER_LOCATION)
    if len(bulkFiles) == 0:
        logging.error("no bulk files available. Downloading default bulk.")  # TODO prompt to download bulk file
        downloadBulkData()
        bulkFiles = os.listdir(constants.DEFAULT_BULK_FOLDER_LOCATION)

    # Expected name : default-cards-20230813090443.json
    mostRecent = (datetime.datetime(datetime.MINYEAR, 1, 1), None)  # (date, filename)
    for bulkFile in bulkFiles:
        parts = bulkFile.split("-")
        bulkType = parts[0]  # Expected : oracle, unique, default, all
        assert bulkType in ["default", "all"]
        itemType = parts[1]  # Expected : cards, artwork (unwanted)
        assert itemType == "cards"
        date = datetime.datetime.strptime(parts[2].split(".")[0], "%Y%m%d%H%M%S")
        if date > mostRecent[0]:
            mostRecent = (date, bulkFile)
    # TODO warn user if bulk data is outdated
    # ! FIXME handle reading of unicode chars : 暴
    if mostRecent[1] is None:
        raise RuntimeError("No valid bulk file found")
    with open(constants.DEFAULT_BULK_FOLDER_LOCATION / mostRecent[1], 'r', encoding="utf-8") as _f:
        data = json.load(_f)

    return data


def downloadBulkData():
    # https://api.scryfall.com/bulk-data
    # sends list of bulk data with link
    bulkURL = "https://api.scryfall.com/bulk-data"
    bulkDataJson = json.loads(requests.get(bulkURL).content)["data"]
    bulkInfo = None
    for _bulkInfo in bulkDataJson:
        if _bulkInfo["type"] == "default_cards":
            bulkInfo = _bulkInfo
            break
    if bulkInfo is None:
        logging.error("Could not find default_cards bulk data")
        return
    dlUrl = bulkInfo["download_uri"]
    r = requests.get(dlUrl, stream=True)
    localPath = Path(constants.DEFAULT_BULK_FOLDER_LOCATION) / dlUrl.split("/")[-1]
    with open(localPath.as_posix(), mode="wb") as file:
        for chunk in r.iter_content(chunk_size=10 * 1024):
            file.write(chunk)


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


@cache_to_disk(1)
def getFormats() -> list:
    card = getRandomCard()  # TODO handle offline mode
    formats = card["legalities"].keys()
    return list(formats)
