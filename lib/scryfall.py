import logging
from pathlib import Path
from cache_to_disk import cache_to_disk

import scrython.cards
from scrython.foundation import ScryfallError

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

import connector  # noqa E402
from card import Card  # noqa E402
from lib import utils  # noqa E402


SEARCH_DICT_KEYS = [
    'order',
    'unique',
    'dir',
    'include_variations',
    'include_extras',
    'include_multilingual',
    'page',
]


def getCardByName(searchDict: dict):
    cards = []

    kwargs = {}
    for k in searchDict.keys():
        if k in SEARCH_DICT_KEYS:
            kwargs.update({k: searchDict.pop(k)})

    try:
        scryfallReq = scrython.cards.Search(q=searchDict["name"], *kwargs)
    except ScryfallError as e:
        logging.warning(e)
    else:
        for cardJson in scryfallReq.scryfallJson["data"]:
            cards.append(Card(cardJson))
    return cards


def getCardReprints(cardId: str):
    card = getCardById(cardId)
    if "sets" not in card.keys():
        reprintsDict = utils.getUrlJsonData(card["prints_search_uri"])
        sets = [_["set"] for _ in reprintsDict["data"]]
        sets = list(set(sets))
        connector.updateCard(cardId, {"sets": sets})
    else:
        sets = card["sets"]
    return sets


def getCardById(id: str):
    card = connector.getCard(id)
    if card is None:
        scryfallReq = scrython.cards.Id(id=id)
        card = Card(scryfallReq.scryfallJson)
        connector.saveCard(id, card)
    else:
        card = card["data"]
    return card


def getSetData(setId, dataKey):
    allSets = getSets()
    possibleSets = [_ for _ in allSets if _["id"] == setId]
    if len(possibleSets) == 1:
        return possibleSets[0][dataKey]
    else:
        raise IndexError("Set ID could not be found")


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
