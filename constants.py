from pathlib import Path

QSPLITTER_HANDLE_WIDTH = 8

DEFAULT_DB_LOCATION = Path.home() / "mtg_org.db"
DEFAULT_CACHE_DB_LOCATION = Path.home() / "mtg_org_cache.db"

DECKS_TABLE_NAME = "Decks"
COLLECTIONS_TABLE_NAME = "Collections"
CARDS_TABLE_NAME = "Cards"

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
    "MTGO",
    "MTG Arena"
]
