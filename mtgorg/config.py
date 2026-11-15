import configparser

import constants


DEFAULT_SCRYFALL_SETTINGS = {
    "use_bulk_files": "false",
    "bulk_auto_update": "true",
    "bulk_language_mode": "english",
}


def configFileExists() -> bool:
    if constants.DEFAULT_CONFIGURATION_FILE.is_file():
        return True
    else:
        return False


def createConfigFile():
    config = configparser.ConfigParser()
    config['WEBDATA'] = {
        "resources_date": ""
    }
    config['SCRYFALL'] = DEFAULT_SCRYFALL_SETTINGS
    with open(constants.DEFAULT_CONFIGURATION_FILE.as_posix(), 'w') as _f:
        config.write(_f)


def readConfig() -> dict:
    config = configparser.ConfigParser()
    config.read(constants.DEFAULT_CONFIGURATION_FILE)
    return {s: dict(config.items(s)) for s in config.sections()}


def writeValue(value, section, item):
    config = configparser.ConfigParser()
    config.read(constants.DEFAULT_CONFIGURATION_FILE)
    if not config.has_section(section):
        config.add_section(section)
    config[section][item] = value
    with open(constants.DEFAULT_CONFIGURATION_FILE.as_posix(), 'w') as _f:
        config.write(_f)


def getScryfallSettings() -> dict:
    settings = {**DEFAULT_SCRYFALL_SETTINGS, **readConfig().get("SCRYFALL", {})}
    languageMode = settings["bulk_language_mode"]
    if languageMode not in constants.BULK_DATA_TYPES:
        languageMode = "english"
    return {
        "use_bulk_files": settings["use_bulk_files"].lower() == "true",
        "bulk_auto_update": settings["bulk_auto_update"].lower() == "true",
        "bulk_language_mode": languageMode,
    }


def saveScryfallSettings(useBulkFiles: bool, autoUpdate: bool, languageMode: str):
    if languageMode not in constants.BULK_DATA_TYPES:
        languageMode = "english"
    writeValue(str(useBulkFiles).lower(), "SCRYFALL", "use_bulk_files")
    writeValue(str(autoUpdate).lower(), "SCRYFALL", "bulk_auto_update")
    writeValue(languageMode, "SCRYFALL", "bulk_language_mode")


def loadScryfallSettings():
    settings = getScryfallSettings()
    constants.USE_BULK_FILES = settings["use_bulk_files"]
    constants.BULK_AUTO_UPDATE = settings["bulk_auto_update"]
    constants.BULK_LANGUAGE_MODE = settings["bulk_language_mode"]
