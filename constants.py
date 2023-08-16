from pathlib import Path

QSPLITTER_HANDLE_WIDTH = 8

DEFAULT_DB_LOCATION = Path.home() / ".mtgo" / "mtg_org.db"
DEFAULT_CACHE_DB_LOCATION = Path.home() / ".mtgo" / "mtg_org_cache.db"
DEFAULT_BULK_FOLDER_LOCATION = Path.home() / ".mtgo" / "scryfall_bulk"

DECKS_TABLE_NAME = "Decks"
COLLECTIONS_TABLE_NAME = "Collections"
CARDS_TABLE_NAME = "Cards"

USE_BULK_FILES = False  # TODO let use choose from gui
# FIXME imports test require False (or full cards list) to work

RARITIES = {
    "common": {
        "color": "#000"
    },
    "uncommon": {
        "color": "#BBB"
    },
    "rare": {
        "color": "#FA0"
    },
    "mythic": {
        "color": "#F40"
    }
}

CURRENCY = [
    # "usd", "$"
    "eur", "€"
]

LANG = ["en", "fr"]

IMPORT_FORMATS = [
    "MTGO .dek",
    "MTG Arena",
    "CSV"
]
