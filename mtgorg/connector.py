import json
import logging
import shutil
import threading
from tinydb import TinyDB, Query
from pathlib import Path

from lib import cachestate, system

import constants


class Collection(dict):
    def __init__(self) -> None:
        ...


class Deck(Collection):
    def __init__(self):
        super().__init__()


_cacheDB: TinyDB | None = None
_cacheDBPath: Path | None = None
_cacheLock = threading.RLock()


def resetCacheDB():
    global _cacheDB, _cacheDBPath
    with _cacheLock:
        _cacheDB = None
        _cacheDBPath = None


def getDB(location: Path = constants.DEFAULT_DB_LOCATION) -> TinyDB:
    if location.is_file() and system.isFileEditable(location):
        return TinyDB(location.as_posix(), sort_keys=True, indent=4)
    else:
        # TODO Ask for db creation location
        return TinyDB(location.as_posix(), sort_keys=True, indent=4)


def getCacheDB(location: Path | None = None) -> TinyDB:
    global _cacheDB, _cacheDBPath
    location = location or constants.DEFAULT_CACHE_DB_LOCATION
    with _cacheLock:
        if _cacheDB is not None and _cacheDBPath == location:
            return _cacheDB
        if location.is_file():
            try:
                with open(location, "r", encoding="utf-8") as file:
                    json.load(file)
            except json.JSONDecodeError as e:
                backup = location.with_suffix(location.suffix + ".corrupt")
                logging.error(f"Card cache is corrupt; backing up to {backup}: {e}")
                shutil.copy2(location, backup)
                location.unlink(missing_ok=True)
        if not (location.is_file() and system.isFileEditable(location)):
            logging.warning("Card cache is missing or not editable; creating a new one")
        _cacheDB = TinyDB(location.as_posix())
        _cacheDBPath = location
        return _cacheDB


# -------------------------------- COLLECTIONS ------------------------------- #

def createCollection(collName, cardList: list | None = None):
    cardList = cardList if cardList is not None else []
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
    if coll is None:
        logging.error(f"Collection {previousCollName=} not found")
        return
    coll["name"] = newCollName
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
        coll, Query().name == previousCollName
    )


def getCollectionsList() -> list:
    collections = getDB().table(constants.COLLECTIONS_TABLE_NAME).all()
    return collections


def getCollection(collectionName) -> dict | None:
    collections = getDB().table(constants.COLLECTIONS_TABLE_NAME).search(Query().name == collectionName)
    if len(collections) == 1:
        return collections[0]
    else:
        return None


def addCardToCollection(collectionName, qty, cardId):
    collection = getCollection(collectionName)
    if collection is None:
        logging.error(f"Collection {collectionName=} not found")
        return
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
    if collection is None:
        logging.error(f"Collection {collectionName=} not found")
        return
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
    if collection is None:
        logging.error(f"Collection {collectionName=} not found")
        return
    cardList = collection["cardList"]
    collection["cardList"] = [_ for _ in cardList if _[1] != cardId]
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(
        collection, Query().name == collectionName
    )


def replaceCardInCollection(collectionName: str, oldCardId: str, newCardId: str):
    collection = getCollection(collectionName)
    if collection is None:
        logging.error(f"Collection {collectionName=} not found")
        return
    cardList = collection["cardList"]
    for entry in cardList:
        if entry[1] == oldCardId:
            entry[1] = newCardId
    collection["cardList"] = cardList
    getDB().table(constants.COLLECTIONS_TABLE_NAME).update(collection, Query().name == collectionName)


# ----------------------------------- DECKS ---------------------------------- #

DECK_SECTION_KEYS = {
    "main": "cardList",
    "sideboard": "sideboard",
    "commander": "commander",
    "companion": "companion",
}


def _deckSectionKey(section: str) -> str:
    return DECK_SECTION_KEYS.get(section, "cardList")


def _getDeckSection(deck: dict, section: str) -> list:
    key = _deckSectionKey(section)
    cardList = deck.get(key)
    if not isinstance(cardList, list):
        cardList = []
        deck[key] = cardList
    return cardList


def createDeck(deckName, cardList: list | None = None, sideboard: list | None = None,
               commander: list | None = None, companion: list | None = None,
               format: str = constants.DEFAULT_DECK_FORMAT, bracket: int | None = None):
    cardList = cardList if cardList is not None else []
    sideboard = sideboard if sideboard is not None else []
    commander = commander if commander is not None else []
    companion = companion if companion is not None else []
    if format not in constants.DECK_FORMATS:
        format = constants.DEFAULT_DECK_FORMAT
    if bracket is not None:
        bracket = int(bracket)
        if bracket < 1 or bracket > 5:
            bracket = None
    if format != "commander":
        bracket = None
    if getDeck(deckName) is None:
        getDB().table(constants.DECKS_TABLE_NAME).insert(
            {
                "name": deckName,
                "format": format,
                "bracket": bracket,
                "cardList": cardList,
                "sideboard": sideboard,
                "commander": commander,
                "companion": companion,
            }
        )
    else:
        logging.error(f"Deck with {deckName=} already exists")


def getDeckBracket(deckName) -> int | None:
    deck = getDeck(deckName)
    if deck is None:
        return None
    return deck.get("bracket")


def setDeckBracket(deckName, bracket: int | None):
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    if bracket is not None:
        bracket = int(bracket)
        if bracket < 1 or bracket > 5:
            logging.error(f"Invalid commander bracket {bracket=}")
            return
    if deck.get("format") != "commander":
        bracket = None
    deck["bracket"] = bracket
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def getDeckFormat(deckName) -> str:
    deck = getDeck(deckName)
    if deck is None:
        return constants.DEFAULT_DECK_FORMAT
    return deck.get("format", constants.DEFAULT_DECK_FORMAT)


def setDeckFormat(deckName, format: str):
    if format not in constants.DECK_FORMATS:
        logging.error(f"Unknown deck format {format=}")
        return
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    deck["format"] = format
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def removeDeck(deckName):
    if getDeck(deckName) is not None:
        getDB().table(constants.DECKS_TABLE_NAME).remove(
            Query().name == deckName
        )


def renameDeck(previousDeckName, newDeckName):
    deck = getDeck(previousDeckName)
    if deck is None:
        logging.error(f"Deck {previousDeckName=} not found")
        return
    deck["name"] = newDeckName
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == previousDeckName
    )


def getDecksList() -> list:
    decks = getDB().table(constants.DECKS_TABLE_NAME).all()
    return decks


def getDeck(deckName) -> dict | None:
    decks = getDB().table(constants.DECKS_TABLE_NAME).search(Query().name == deckName)
    if len(decks) == 1:
        return decks[0]
    return None


def getDeckSection(deckName, section: str = "main") -> list:
    deck = getDeck(deckName)
    if deck is None:
        return []
    return _getDeckSection(deck, section)


def addCardToDeck(deckName, qty, cardId, section: str = "main"):
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    cardList = _getDeckSection(deck, section)

    if len([_[1] for _ in cardList if _[1] == cardId]) == 0:
        cardList.append((qty, cardId))
    else:
        for card in cardList:
            if card[1] == cardId:
                card[0] += qty
                break
    deck[_deckSectionKey(section)] = cardList
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def changeCardDeckQty(deckName, qty, cardId, section: str = "main"):
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    cardList = _getDeckSection(deck, section)
    for card in cardList:
        if card[1] == cardId:
            card[0] = qty
    deck[_deckSectionKey(section)] = cardList
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def removeCardFromDeck(deckName, cardId, section: str = "main"):
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    cardList = _getDeckSection(deck, section)
    deck[_deckSectionKey(section)] = [_ for _ in cardList if _[1] != cardId]
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def moveCardInDeck(deckName: str, cardId: str, fromSection: str, toSection: str):
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    if fromSection == toSection:
        return
    source = _getDeckSection(deck, fromSection)
    target = _getDeckSection(deck, toSection)
    movedQty = None
    for entry in list(source):
        if entry[1] == cardId:
            movedQty = int(entry[0])
            source.remove(entry)
            break
    if movedQty is None:
        return
    for entry in target:
        if entry[1] == cardId:
            entry[0] += movedQty
            break
    else:
        target.append((movedQty, cardId))
    deck[_deckSectionKey(fromSection)] = source
    deck[_deckSectionKey(toSection)] = target
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


def replaceCardInDeck(deckName: str, oldCardId: str, newCardId: str, section: str = "main"):
    deck = getDeck(deckName)
    if deck is None:
        logging.error(f"Deck {deckName=} not found")
        return
    cardList = _getDeckSection(deck, section)
    for entry in cardList:
        if entry[1] == oldCardId:
            entry[1] = newCardId
    deck[_deckSectionKey(section)] = cardList
    getDB().table(constants.DECKS_TABLE_NAME).update(
        deck, Query().name == deckName
    )


# ----------------------------------- CACHE ---------------------------------- #


def _cardQuery(cardId):
    return (Query().id == cardId) & (Query().generation == cachestate.getCardGeneration())


def getCard(cardId) -> dict | None:
    with _cacheLock:
        card = getCacheDB().table(constants.CARDS_TABLE_NAME).search(_cardQuery(cardId))
        if len(card) == 0:
            card = None
        elif len(card) == 1:
            card = card[0]
        else:
            card = card[0]
            logging.warning(f"Got multiple entries for card id {cardId}")
    return card


def saveCard(cardId, cardData) -> None:
    with _cacheLock:
        table = getCacheDB().table(constants.CARDS_TABLE_NAME)
        if len(table.search(_cardQuery(cardId))) == 0:
            table.insert({"data": cardData, "id": cardId, "generation": cachestate.getCardGeneration()})
        else:
            table.update({"data": cardData}, _cardQuery(cardId))


def updateCard(cardId, updateDict: dict) -> None:
    with _cacheLock:
        card = getCard(cardId)
        if card is None:
            logging.error(f"Card {cardId=} not found in cache")
            return
        cardData = card["data"]
        cardData.update(updateDict)
        getCacheDB().table(constants.CARDS_TABLE_NAME).update({"data": cardData}, _cardQuery(cardId))


def pruneOldCards() -> None:
    """Remove cached cards from previous generations."""
    with _cacheLock:
        generation = cachestate.getCardGeneration()
        getCacheDB().table(constants.CARDS_TABLE_NAME).remove(
            lambda card: card.get("generation") != generation
        )


def _removeCachedFile(path: Path) -> tuple[int, int, str | None]:
    try:
        size = path.stat().st_size
        path.unlink()
        return 1, size, None
    except OSError as e:
        logging.error(f"Could not remove cache file {path}: {e}")
        return 0, 0, str(e)


def clearCache() -> dict:
    """Delete cached card data, images, set icons, and set metadata."""
    resetCacheDB()
    filesRemoved = 0
    bytesRemoved = 0
    errors = []

    targets = [
        constants.DEFAULT_CACHE_DB_LOCATION,
        constants.DEFAULT_INFOS_LOCATION / "sets.json",
        cachestate.statePath(),
    ]
    for folder in (constants.DEFAULT_CARDIMAGES_LOCATION, constants.DEFAULT_SET_ICONS_LOCATION):
        if folder.is_dir():
            targets.extend(path for path in folder.iterdir() if path.is_file())
    if constants.DEFAULT_BULK_FOLDER_LOCATION.is_dir():
        targets.extend(constants.DEFAULT_BULK_FOLDER_LOCATION.glob("*-cache.sqlite3*"))

    for target in targets:
        if not target.is_file():
            continue
        removed, size, error = _removeCachedFile(target)
        filesRemoved += removed
        bytesRemoved += size
        if error is not None:
            errors.append(error)

    return {"files": filesRemoved, "bytes": bytesRemoved, "errors": errors}


def _fileSize(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def _folderSize(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    total = 0
    for path in folder.iterdir():
        if path.is_file():
            total += _fileSize(path)
    return total


def getStorageStats() -> dict:
    """Return byte sizes for the user database and local caches."""
    bulkFiles = 0
    bulkIndex = 0
    if constants.DEFAULT_BULK_FOLDER_LOCATION.is_dir():
        for path in constants.DEFAULT_BULK_FOLDER_LOCATION.iterdir():
            if not path.is_file():
                continue
            if "-cache.sqlite3" in path.name:
                bulkIndex += _fileSize(path)
            else:
                bulkFiles += _fileSize(path)
    return {
        "decks": _fileSize(constants.DEFAULT_DB_LOCATION),
        "card_cache": _fileSize(constants.DEFAULT_CACHE_DB_LOCATION),
        "images": _folderSize(constants.DEFAULT_CARDIMAGES_LOCATION),
        "set_icons": _folderSize(constants.DEFAULT_SET_ICONS_LOCATION),
        "set_metadata": _fileSize(constants.DEFAULT_INFOS_LOCATION / "sets.json"),
        "bulk_files": bulkFiles,
        "bulk_index": bulkIndex,
    }
