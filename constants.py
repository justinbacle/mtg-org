from pathlib import Path

QSPLITTER_HANDLE_WIDTH = 8

DEFAULT_DB_LOCATION = Path.home() / "mtg_org.db"

DECKS_TABLE_NAME = "Decks"
COLLECTIONS_TABLE_NAME = "Collections"

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
