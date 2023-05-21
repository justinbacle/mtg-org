import logging
import klepto

import scrython.cards
from scrython.foundation import ScryfallError

import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from card import Card  # noqa E402


@klepto.lru_cache(maxsize=1000)
def getCardByName(name: str):
    try:
        scryfallReq = scrython.cards.Named(fuzzy=name)
        card = Card(scryfallReq.scryfallJson)
    except ScryfallError as e:
        logging.warning(e)
        card = {}
    return card


@klepto.lru_cache(maxsize=1000)
def getCardById(id: str):
    scryfallReq = scrython.cards.Id(id=id)
    card = Card(scryfallReq.scryfallJson)
    print(card)
    return card


if __name__ == "__main__":
    getCardByName("Imoti")
    getCardById("8afceb13-877a-4256-9ba6-851b6924ffd9")
