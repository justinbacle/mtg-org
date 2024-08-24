import configparser

import constants


def configFileExists() -> bool:
    if constants.DEFAULT_CONFIGURATION_FILE.is_file() and constants.DEFAULT_CONFIGURATION_FILE.exists():
        return True
    else:
        return False


def createConfigFile():
    config = configparser.ConfigParser()
    config['WEBDATA'] = {
        "resources_date": ""
    }
    with open(constants.DEFAULT_CONFIGURATION_FILE.as_posix(), 'w') as _f:
        config.write(_f)


def readConfig() -> dict:
    config = configparser.ConfigParser()
    config.read(constants.DEFAULT_CONFIGURATION_FILE)
    return {s: dict(config.items(s)) for s in config.sections()}


def writeValue(value, section, item):
    config = configparser.ConfigParser()
    config.read(constants.DEFAULT_CONFIGURATION_FILE)
    config[section][item] = value
    with open(constants.DEFAULT_CONFIGURATION_FILE.as_posix(), 'w') as _f:
        config.write(_f)
