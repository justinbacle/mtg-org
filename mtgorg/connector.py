import logging
from tinydb import TinyDB, Query
from pathlib import Path

from mtgorg.lib import system

from mtgorg import constants


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


# -------------------------------- COLLECTIONS ------------------------------- #

def createCollection(collName, cardList: list = []):
    if getCollection(collName) is None:
        getDB().table(constants.COLLECTIONS_TABLE_NAME).insert(
            {
                "name": collName,
                "cardList": cardList
            }
        )
    else:
        logging.error(f"Collection with {collName=} already exists")


def removeCollection(collName):
    if getCollection(collName) is not None:
        getDB().table(constants.COLLECTIONS_TABLE_NAME).remove(
            Query().name == collName
        )


def renameCollection(previousCollName, newCollName):
    coll = getCollection(previousCollName)
    coll["name"] = newCollName
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
        coll, Query().name == previousCollName
    )


def getCollectionsList() -> list:
    collections = getDB().table(constants.COLLECTIONS_TABLE_NAME).all()
    return collections


def getCollection(collectionName) -> Deck:
    collections = getDB().table(constants.COLLECTIONS_TABLE_NAME).search(Query().name == collectionName)
    if len(collections) == 1:
        return collections[0]
    else:
        return None


def addCardToCollection(collectionName, qty, cardId):
    collection = getCollection(collectionName)
    cardList = collection["cardList"]
    # If card not in collection
    if len([_[0] for _ in cardList if _[1] == cardId]) == 0:
        collection.update(
            {"cardList": cardList + [(qty, cardId)]}
        )
        getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
            collection, Query().name == collectionName
        )
    else:
        previousQty = [_[0] for _ in cardList if _[1] == cardId][0]
        changeCardCollectionQty(collectionName, previousQty + 1, cardId)


def changeCardCollectionQty(collectionName, qty, cardId):
    collection = getCollection(collectionName)
    cardList = collection["cardList"]
    for card in cardList:
        if card[1] == cardId:
            card[0] = qty
    collection["cardList"] = cardList
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
        collection, Query().name == collectionName
    )


def removeCardFromCollection(collectionName, cardId):
    collection = getCollection(collectionName)
    cardList = collection["cardList"]
    collection["cardList"] = [_ for _ in cardList if _[1] != cardId]
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
        collection, Query().name == collectionName
    )


# ----------------------------------- DECKS ---------------------------------- #
# TODO: handle commander/sideboard etc in card list
# cardlist : (qty, id) ->  (qty, id, zone)


def createDeck(deckName, cardList: list = []):
    if getDeck(deckName) is None:
        getDB().table(constants.DECKS_TABLE_NAME).insert(
            {
                "name": deckName,
                "cardList": cardList
            }
        )
    else:
        logging.error(f"Deck with {deckName=} already exists")


def removeDeck(deckName):
    if getDeck(deckName) is not None:
        getDB().table(constants.DECKS_TABLE_NAME).remove(
            Query().name == deckName
        )


def renameDeck(previousDeckName, newDeckName):
    deck = getDeck(previousDeckName)
    deck["name"] = newDeckName
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == previousDeckName
    )


def getDecksList() -> list:
    decks = getDB().table(constants.DECKS_TABLE_NAME).all()
    return decks


def getDeck(deckName) -> Deck:
    decks = getDB().table(constants.DECKS_TABLE_NAME).search(Query().name == deckName)
    if len(decks) == 1:
        return decks[0]


def addCardToDeck(deckName, qty, cardId):
    deck = getDeck(deckName)
    cardList = deck["cardList"]

    # If card not in deck
    if len([_[0] for _ in cardList if _[1] == cardId]) == 0:
        deck.update(
            {"cardList": cardList + [(qty, cardId)]}
        )
        getDB().table(constants.DECKS_TABLE_NAME).update(
            deck, Query().name == deckName
        )
    else:
        previousQty = [_[0] for _ in cardList if _[1] == cardId][0]
        changeCardDeckQty(deckName, previousQty + 1, cardId)


def changeCardDeckQty(deckName, qty, cardId):
    deck = getDeck(deckName)
    cardList = deck["cardList"]
    for card in cardList:
        if card[1] == cardId:
            card[0] = qty
    deck["cardList"] = cardList
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def removeCardFromDeck(deckName, cardId):
    deck = getDeck(deckName)
    cardList = deck["cardList"]
    deck["cardList"] = [_ for _ in cardList if _[1] != cardId]
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


# ----------------------------------- CACHE ---------------------------------- #


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
    if len(getCacheDB().table(constants.CARDS_TABLE_NAME).search(Query().id == cardId)) == 0:
        getCacheDB().table(constants.CARDS_TABLE_NAME).insert(
            {"data": cardData, "id": cardId}
        )
    else:
        updateCard(cardId, cardData)


def updateCard(cardId, updateDict: dict) -> None:
    cardData = getCard(cardId)["data"]
    cardData.update(updateDict)
    getCacheDB().table(constants.CARDS_TABLE_NAME).update({"data": cardData}, Query().id == cardId)
