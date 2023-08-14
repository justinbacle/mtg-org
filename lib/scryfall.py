import datetime
import logging
import json
from pathlib import Path
from cache_to_disk import cache_to_disk
from tqdm import tqdm
from fuzzywuzzy import fuzz  # install python-Levenshtein for faster results

import scrython.cards
from scrython.foundation import ScryfallError

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

import connector  # noqa E402
from card import Card  # noqa E402
from lib import utils  # noqa E402
import constants  # noqa E402


SEARCH_DICT_KEYS = [
    'order',
    'unique',
    'dir',
    'include_variations',
    'include_extras',
    'include_multilingual',
    'page',
]


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
        for id, name in tqdm([(_["id"], _["name"]) for _ in getBulkData()]):
            if fuzz.ratio(searchDict["name"], name) >= 60:
                cards.append(getCardById(id))
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
        elif k == "name" and exact:  # https://scryfall.com/docs/syntax#exact
            q += "!\"" + v + "\" "
        else:
            q += k + ":" + v + " "

    try:
        scryfallReq = scrython.cards.Search(q=q, **kwargs)
    except ScryfallError as e:
        logging.warning(e)
    else:
        for cardJson in scryfallReq.scryfallJson["data"]:
            cards.append(Card(cardJson))
    return cards


def getCardReprints(cardId: str):
    card = getCardById(cardId)
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


def getCardReprintId(cardId: str, set: str, lang: str = "en"):
    # TODO add cache ?
    card = getCardById(cardId)
    reprintsDict = utils.getUrlJsonData(card["prints_search_uri"])
    ids = [_["id"] for _ in reprintsDict["data"] if _["set"] == set]
    while reprintsDict["has_more"]:
        reprintsDict = utils.getUrlJsonData(reprintsDict["next_page"])
        ids += [_["id"] for _ in reprintsDict["data"] if _["set"] == set]
    correctEnId = ids[0]  # Todo handle mutiple matches (e.g. basic lands)
    if lang != "en":
        try:
            foundCard = scrython.cards.Collector(
                code=set, collector_number=getCardById(correctEnId)["collector_number"], lang=lang).scryfallJson
            returnId = foundCard["id"]
        except ScryfallError:
            logging.warning(f"Could not find {lang=} translation for given set")
            returnId = correctEnId
    else:
        returnId = correctEnId

    return returnId


def getCardById(id: str):
    card = connector.getCard(id)
    if card is None:  # card not in Cache
        if constants.USE_BULK_FILES:
            card = list(filter(lambda x: x["id"] == id, getBulkData()))[0]
        else:
            scryfallReq = scrython.cards.Id(id=id)
            card = Card(scryfallReq.scryfallJson)
        connector.saveCard(id, card)
    else:
        card = card["data"]
    return card


def getCardByMTGOId(mtgoId: int) -> dict:
    if constants.USE_BULK_FILES:
        cardData = list(filter(lambda x: x["mtgo_id"] == mtgoId, getBulkData()))[0]
    else:
        url = f"https://api.scryfall.com/cards/mtgo/{mtgoId}"
        cardData = utils.getUrlJsonData(url)
    return cardData


def getRandomCard() -> str:
    return scrython.Random().scryfallJson


def getSetData(setId, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["id"] == setId]
    if len(possibleSets) == 1:
        return possibleSets[0][dataKey]
    else:
        raise IndexError("Set ID could not be found")


def getSetDataByCode(setCode, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["code"] == setCode]
    if len(possibleSets) == 1:
        return possibleSets[0][dataKey]
    else:
        raise IndexError("Set code could not be found")


def getSetSymbol(setId):
    return getSetData(setId, "icon_svg_uri")


def getSetSvg(setId):
    setIconFilePath = Path(f"resources/icons/sets/{setId}.svg")
    if not (setIconFilePath.is_file() and os.access(setIconFilePath, os.R_OK)):
        svgData = utils.getUrlData(getSetSymbol(setId))
        f = open(setIconFilePath, 'w')
        f.write(svgData)
        f.close()
    return setIconFilePath.as_posix()


def getSetReleaseYear(setId):
    releaseDate = getSetData(setId, "released_at")
    return releaseDate.split("-")[0]


@cache_to_disk(1)
def getSets() -> list:
    sets = scrython.Sets()
    return sets.scryfallJson["data"]


@cache_to_disk(1)
def getBulkData():  # TODO load into a tinyDB object ?
    bulkFiles = os.listdir(constants.DEFAULT_BULK_FOLDER_LOCATION)
    if len(bulkFiles) == 0:
        logging.error("no bulk files available")  # TODO prompt to download bulk file
        raise NotImplementedError
    else:
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
        with open(constants.DEFAULT_BULK_FOLDER_LOCATION / bulkFile, 'r') as _f:
            data = json.load(_f)
    return data


def downloadBulkData():
    # https://api.scryfall.com/bulk-data
    # sends list of bulk data with link
    ...
