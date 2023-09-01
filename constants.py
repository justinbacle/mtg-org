from pathlib import Path

QSPLITTER_HANDLE_WIDTH = 8

DEFAULT_ROOT_USER_FOLDER = Path.home() / ".mtgo"
DEFAULT_DB_LOCATION = DEFAULT_ROOT_USER_FOLDER / "mtg_org.db"
DEFAULT_CACHE_DB_LOCATION = DEFAULT_ROOT_USER_FOLDER / "mtg_org_cache.db"
DEFAULT_BULK_FOLDER_LOCATION = DEFAULT_ROOT_USER_FOLDER / "scryfall_bulk"
DEFAULT_INFOS_LOCATION = DEFAULT_ROOT_USER_FOLDER / "infos"
DEFAULT_FONTS_LOCATION = DEFAULT_ROOT_USER_FOLDER / "fonts"
DEFAULT_SET_ICONS_LOCATION = DEFAULT_ROOT_USER_FOLDER / "sets_icons"
DEFAULT_CARDIMAGES_LOCATION = DEFAULT_ROOT_USER_FOLDER / "card_imgs"

DECKS_TABLE_NAME = "Decks"
COLLECTIONS_TABLE_NAME = "Collections"
CARDS_TABLE_NAME = "Cards"

TIME_FORMAT_STR = "%Y-%m-%d %H:%M:%S"

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

LANGS = {  # Default one on top
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "zhs": "Simplified Chinese",
    "zht": "Traditional Chinese",
    # "he": "Hebrew",  # 1 card
    # "la": "Latin",  # 1 card
    # "grc": "Ancient Greek",  # 1 card, Not working ?
    # "ar": "Arabic",  # 1 card
    # "sa": "Sanskrit",  # 1 card
    "ph": "Phyrexian"
}

IMPORT_FORMATS = [
    "MTGO .dek",
    "MTG Arena",
    "CSV"
]
