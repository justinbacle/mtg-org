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
    inputStr.replace("{W}", "&#xe600;")
    inputStr.replace("{U}", "&#xe601;")
    inputStr.replace("{B}", "&#xe602;")
    inputStr.replace("{R}", "&#xe603;")
    inputStr.replace("{G}", "&#xe604;")
    inputStr = re.sub(r"{(\d)}", r"\g<1>", inputStr)
    return inputStr
