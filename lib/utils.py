import requests
import functools
import operator
from dotmap import DotMap
import re


def getSvgData(url):
    if url is not None:
        r = requests.get(url)
        return r.text


def getFromDict(dataDict: dict, mapList: list, default=None):
    ''' get a value in dict with a map list (list of keys)'''
    # TODO : which behavior is wanted, for now does not make a deep copy of the dict
    # Ensure the original dict is not modified (handles the case of DotMap)
    if isinstance(dataDict, DotMap):
        dataDictCopy = dict(**dataDict.toDict())
    else:
        dataDictCopy = dict(dataDict)

    try:
        value = functools.reduce(operator.getitem, mapList, dataDictCopy)
    except (KeyError, TypeError):
        value = default

    if isinstance(dataDict, DotMap) and isinstance(value, dict):
        value = DotMap(value)

    if isinstance(dataDict, DotMap) and value == {}:
        value = default

    return value


def setManaText(inputStr) -> str:

    # Mana
    # if len(re.findall(r"{(\d)}", inputStr)) > 0:
    #     for match in re.findall(r"{(\d)}", inputStr):
    #         inputStr = inputStr.replace("{" + match + "}", match)
            # inputStr = re.fin(r"{(\d)}", r"\g<1>", inputStr)  #noqa E800

    # for mana_symbol, replacement in MANA_SYMBOLS.items():
    #     _pre = "<font face=\"Mana\">"
    #     _post = "</font>"
    #     if mana_symbol in inputStr:
    #         inputStr = inputStr.replace(mana_symbol, replacement)

    # NDPMTG
    # TODO change qtablewidget item NDPMTG_SYMBOLS so that it can host a qlabel with multiple fonts ?
    # for mana_symbol, replacement in NDPMTG_SYMBOLS.items():
    #     _pre = "<font face=\"NDPMTG\">"
    #     _post = "</font>"
    #     if mana_symbol in inputStr:
    #         inputStr = inputStr.replace(mana_symbol, replacement)
    return inputStr


MANA_SYMBOLS = {
    "{W}": "&#xe600;",
    "{U}": "&#xe601;",
    "{B}": "&#xe602;",
    "{R}": "&#xe603;",
    "{G}": "&#xe604;"
}

# Dictionary of symbols as they appear in oracle text, and their corresponding symbols to look correct in NDPMTG font
NDPMTG_SYMBOLS = {
    "{W/P}": "Qp",
    "{U/P}": "Qp",
    "{B/P}": "Qp",
    "{R/P}": "Qp",
    "{G/P}": "Qp",
    "{E}": "e",
    "{T}": "ot",
    "{X}": "ox",
    "{0}": "o0",
    "{1}": "o1",
    "{2}": "o2",
    "{3}": "o3",
    "{4}": "o4",
    "{5}": "o5",
    "{6}": "o6",
    "{7}": "o7",
    "{8}": "o8",
    "{9}": "o9",
    "{10}": "oA",
    "{11}": "oB",
    "{12}": "oC",
    "{13}": "oD",
    "{14}": "oE",
    "{15}": "oF",
    "{16}": "oG",
    "{20}": "oK",
    "{W}": "ow",
    "{U}": "ou",
    "{B}": "ob",
    "{R}": "or",
    "{G}": "og",
    "{C}": "oc",
    "{W/U}": "QqLS",
    "{U/B}": "QqMT",
    "{B/R}": "QqNU",
    "{R/G}": "QqOV",
    "{G/W}": "QqPR",
    "{W/B}": "QqLT",
    "{B/G}": "QqNV",
    "{G/U}": "QqPS",
    "{U/R}": "QqMU",
    "{R/W}": "QqOR",
    "{2/W}": "QqWR",
    "{2/U}": "QqWS",
    "{2/B}": "QqWT",
    "{2/R}": "QqWU",
    "{2/G}": "QqWV",
    "{S}": "omn",
    "{Q}": "ol",
    "{CHAOS}": "?"
}
