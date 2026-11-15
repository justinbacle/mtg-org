import os
import sys
from pathlib import Path

# ------------------------------------ QT ------------------------------------ #
THEME = "fusion"
AUTO_CHECK_UPDATES = True
THEMES = {
    "fusion": "Fusion",
    "kde": "System (KDE)",
    "material": "Material",
}


def kdeThemeAvailable() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    return "kde" in desktop or bool(os.environ.get("KDE_FULL_SESSION"))


def availableThemes() -> dict:
    return {key: label for key, label in THEMES.items() if key != "kde" or kdeThemeAvailable()}


IMG_DOWNLOAD_METHOD = "qt"  # ["direct", "qt"]
IMG_SIZE = "large"  # small, normal, large, png
QSPLITTER_HANDLE_WIDTH = 6

# ----------------------------------- UTILS ---------------------------------- #
DATETIME_FORMAT = "%d/%m/%y %H:%M:%S"

# ----------------------------------- PATHS ---------------------------------- #
DEFAULT_ROOT_USER_FOLDER = Path.home() / ".mtgo"
DEFAULT_CONFIGURATION_FILE = DEFAULT_ROOT_USER_FOLDER / "settings.ini"
DEFAULT_DB_LOCATION = DEFAULT_ROOT_USER_FOLDER / "mtg_org.db"
DEFAULT_CACHE_DB_LOCATION = DEFAULT_ROOT_USER_FOLDER / "mtg_org_cache.db"
DEFAULT_BULK_FOLDER_LOCATION = DEFAULT_ROOT_USER_FOLDER / "scryfall_bulk"
DEFAULT_INFOS_LOCATION = DEFAULT_ROOT_USER_FOLDER / "infos"
DEFAULT_FONTS_LOCATION = DEFAULT_ROOT_USER_FOLDER / "fonts"
DEFAULT_SET_ICONS_LOCATION = DEFAULT_ROOT_USER_FOLDER / "sets_icons"
DEFAULT_CARDIMAGES_LOCATION = DEFAULT_ROOT_USER_FOLDER / "card_imgs"


def appVersion() -> str:
    import json
    path = resourcePath("build_info.json")
    if path.is_file():
        try:
            return str(json.loads(path.read_text(encoding="utf-8")).get("version", "0.1.dev"))
        except (OSError, ValueError):
            pass
    return "0.1.dev"


def resourcePath(*parts: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)
    else:
        root = Path(__file__).resolve().parent.parent
    return root.joinpath("resources", *parts)


# ------------------------------------ DB ------------------------------------ #
DECKS_TABLE_NAME = "Decks"
COLLECTIONS_TABLE_NAME = "Collections"
CARDS_TABLE_NAME = "Cards"
TIME_FORMAT_STR = "%Y-%m-%d %H:%M:%S"

# ------------------------------- Local/Online ------------------------------- #
BULK_DATA_TYPES = {
    "english": "default_cards",
    "all": "all_cards",
}
USE_BULK_FILES = False  # Overridden from settings.ini at startup
BULK_LANGUAGE_MODE = "english"
BULK_AUTO_UPDATE = True
BULK_METADATA_FILENAME = "bulk_info.json"
BULK_INFO_CACHE_SECONDS = 3600

# ---------------------------------- SEARCH ---------------------------------- #
SEARCH_RESULT_LIMIT = 100

# ----------------------------------- DECKS ---------------------------------- #
DECK_FORMATS = {
    "casual": {
        "label": "Casual",
        "sideboard": True,
        "commander": True,
        "maxSideboard": None,
        "deckSize": None,
        "singleton": False,
        "commanderMin": 0,
        "commanderMax": 2,
    },
    "standard": {
        "label": "Standard",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 60,
        "singleton": False,
    },
    "pioneer": {
        "label": "Pioneer",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 60,
        "singleton": False,
    },
    "modern": {
        "label": "Modern",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 60,
        "singleton": False,
    },
    "legacy": {
        "label": "Legacy",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 60,
        "singleton": False,
    },
    "vintage": {
        "label": "Vintage",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 60,
        "singleton": False,
    },
    "pauper": {
        "label": "Pauper",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 60,
        "singleton": False,
    },
    "commander": {
        "label": "Commander",
        "sideboard": False,
        "commander": True,
        "companion": True,
        "maxSideboard": 0,
        "deckSize": 100,
        "singleton": True,
        "commanderMin": 1,
        "commanderMax": 2,
    },
    "brawl": {
        "label": "Brawl",
        "sideboard": False,
        "commander": True,
        "companion": True,
        "maxSideboard": 0,
        "deckSize": 60,
        "singleton": True,
        "commanderMin": 1,
        "commanderMax": 2,
    },
    "historicbrawl": {
        "label": "Historic Brawl",
        "sideboard": False,
        "commander": True,
        "companion": True,
        "maxSideboard": 0,
        "deckSize": 100,
        "singleton": True,
        "commanderMin": 1,
        "commanderMax": 2,
    },
    "oathbreaker": {
        "label": "Oathbreaker",
        "sideboard": False,
        "commander": True,
        "companion": True,
        "maxSideboard": 0,
        "deckSize": 60,
        "singleton": True,
        "commanderMin": 1,
        "commanderMax": 2,
    },
    "limited": {
        "label": "Limited",
        "sideboard": True,
        "commander": False,
        "maxSideboard": 15,
        "deckSize": 40,
        "singleton": False,
    },
}

DEFAULT_DECK_FORMAT = "casual"

# ------------------------------------ MTG ----------------------------------- #
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
    },
    "special": {
        "color": "#748"
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
    "CSV",
    "EDHRec url",
]

MAIN_CARD_TYPES = [
    "creature", "land", "instant", "sorcery", "artifact", "enchantment", "planeswalker", "tribal"
]
