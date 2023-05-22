import logging
import klepto
from pathlib import Path

import scrython.cards
from scrython.foundation import ScryfallError

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from card import Card  # noqa E402
from lib import utils  # noqa E402


@klepto.lru_cache(maxsize=1000)
def getCardByName(name: str):
    cards = []
    try:
        scryfallReq = scrython.cards.Search(q=name)
    except ScryfallError as e:
        logging.warning(e)
    else:
        for cardJson in scryfallReq.scryfallJson["data"]:
            cards.append(Card(cardJson))
    return cards


@klepto.lru_cache(maxsize=1000)
def getCardById(id: str):
    scryfallReq = scrython.cards.Id(id=id)
    card = Card(scryfallReq.scryfallJson)
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
        svgData = utils.getSvgData(getSetSymbol(setId))
        f = open(setIconFilePath, 'w')
        f.write(svgData)
        f.close()
    return setIconFilePath.as_posix()


def getSetReleaseDate(setId):
    return getSetData(setId, "released_at")


@klepto.lru_cache(maxsize=10)
def getSets() -> list:
    sets = scrython.Sets()
    return sets.scryfallJson["data"]
