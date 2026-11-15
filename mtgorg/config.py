import configparser

import constants


DEFAULT_SCRYFALL_SETTINGS = {
    "use_bulk_files": "false",
    "bulk_auto_update": "true",
    "bulk_language_mode": "english",
}

DEFAULT_SEARCH_SETTINGS = {
    "result_limit": "100",
}

DEFAULT_UI_SETTINGS = {
    "theme": "fusion",
    "onboarding_done": "false",
}

DEFAULT_UPDATE_SETTINGS = {
    "auto_check": "true",
    "last_check": "",
    "skipped_version": "",
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
    config['SEARCH'] = DEFAULT_SEARCH_SETTINGS
    config['UI'] = DEFAULT_UI_SETTINGS
    config['UPDATES'] = DEFAULT_UPDATE_SETTINGS
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


def getSearchSettings() -> dict:
    settings = {**DEFAULT_SEARCH_SETTINGS, **readConfig().get("SEARCH", {})}
    try:
        resultLimit = int(settings["result_limit"])
    except (TypeError, ValueError):
        resultLimit = int(DEFAULT_SEARCH_SETTINGS["result_limit"])
    return {"result_limit": max(1, resultLimit)}


def saveSearchSettings(resultLimit: int):
    writeValue(str(max(1, int(resultLimit))), "SEARCH", "result_limit")


def loadSearchSettings():
    constants.SEARCH_RESULT_LIMIT = getSearchSettings()["result_limit"]


def getUISettings() -> dict:
    settings = {**DEFAULT_UI_SETTINGS, **readConfig().get("UI", {})}
    theme = settings.get("theme", "fusion")
    if theme not in constants.availableThemes():
        theme = "fusion"
    return {
        "theme": theme,
        "onboarding_done": settings.get("onboarding_done", "false").lower() == "true",
    }


def saveUISettings(theme: str, onboardingDone: bool | None = None):
    if theme not in constants.availableThemes():
        theme = "fusion"
    writeValue(theme, "UI", "theme")
    if onboardingDone is not None:
        writeValue(str(onboardingDone).lower(), "UI", "onboarding_done")


def loadUISettings():
    constants.THEME = getUISettings()["theme"]


def getUpdateSettings() -> dict:
    settings = {**DEFAULT_UPDATE_SETTINGS, **readConfig().get("UPDATES", {})}
    return {
        "auto_check": settings.get("auto_check", "true").lower() == "true",
        "last_check": settings.get("last_check", ""),
        "skipped_version": settings.get("skipped_version", ""),
    }


def saveUpdateSettings(autoCheck: bool, skippedVersion: str | None = None):
    writeValue(str(autoCheck).lower(), "UPDATES", "auto_check")
    if skippedVersion is not None:
        writeValue(skippedVersion, "UPDATES", "skipped_version")


def saveUpdateCheck(checkedAt: str):
    writeValue(checkedAt, "UPDATES", "last_check")


def loadUpdateSettings():
    constants.AUTO_CHECK_UPDATES = getUpdateSettings()["auto_check"]
