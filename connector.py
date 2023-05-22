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
