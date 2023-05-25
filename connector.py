import logging
from tinydb import TinyDB, Query
from pathlib import Path

from lib import system

import constants


class Collection(dict):
    def __init__(self) -> None:
        ...


class Deck(Collection):
    def __init__(self):
        super().__init__()


def getDB(location: Path = constants.DEFAULT_DB_LOCATION) -> TinyDB:
    if location.is_file() and system.isFileEditable(location):
        return TinyDB(location.as_posix(), sort_keys=True, indent=4)
    else:
        # TODO Ask for db creation location
        return TinyDB(location.as_posix(), sort_keys=True, indent=4)


def getCacheDB(location: Path = constants.DEFAULT_CACHE_DB_LOCATION) -> TinyDB:
    if location.is_file() and system.isFileEditable(location):
        return TinyDB(location.as_posix())
    else:
        # TODO Ask for db creation location
        return TinyDB(location.as_posix())


def getDecksList() -> list:
    decks = getDB().table(constants.DECKS_TABLE_NAME).all()
    return decks


def getDeck(deckName) -> Deck:
    decks = getDB().table(constants.DECKS_TABLE_NAME).search(Query().name == deckName)
    if len(decks) == 1:
        return decks[0]


def getCollectionsList() -> list:
    collections = getDB().table(constants.COLLECTIONS_TABLE_NAME).all()
    return collections


def getCollection(collectionName) -> Deck:
    collections = getDB().table(constants.COLLECTIONS_TABLE_NAME).search(Query().name == collectionName)
    if len(collections) == 1:
        return collections[0]


def addCardToDeck(deckName, qty, cardId):
    deck = getDeck(deckName)
    cardList = deck["cardList"]
    deck.update(
        {"cardList": cardList + [(qty, cardId)]}
    )
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def addCardToCollection(collectionName, qty, cardId):
    collection = getCollection(collectionName)
    cardList = collection["cardList"]
    collection.update(
        {"cardList": cardList + [(qty, cardId)]}
    )
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
        collection, Query().name == collectionName
    )


def getCard(cardId) -> dict:
    card = getCacheDB().table(constants.CARDS_TABLE_NAME).search(Query().id == cardId)
    if len(card) == 0:
        card = None
    elif len(card) == 1:
        card = card[0]
    else:
        card = card[0]
        logging.warning(f"Got multiple entries for card id {cardId}")

    return card


def saveCard(cardId, cardData) -> None:
    getCacheDB().table(constants.CARDS_TABLE_NAME).insert(
        {"data": cardData, "id": cardId}
    )
