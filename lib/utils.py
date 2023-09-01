import os
import requests
import functools
import operator
from dotmap import DotMap
import json
import platform
from pathlib import Path
import html
from bs4 import BeautifulSoup

import constants


# --------------------------------- Platform --------------------------------- #

def isWin() -> bool:
    if platform.system() == 'Windows':
        return True
    else:
        return False


def isLinux() -> bool:
    if platform.system() == 'Linux':
        return True
    else:
        return False


def isMac() -> bool:
    if platform.system() == 'Darwin':
        return True
    else:
        return False


# -------------------------------- Misc utils -------------------------------- #

def getUrlData(url):
    if url is not None:
        r = requests.get(url)
        return r.text


def getUrlJsonData(url):
    text = getUrlData(url)
    jsonData = json.loads(text)
    return jsonData


def loadJson(jsonPath: str | Path):
    if not isinstance(jsonPath, Path):
        jsonPath = Path(jsonPath)
    if jsonPath.is_file():
        with open(jsonPath) as _file:
            file_contents = _file.read()
        return json.loads(file_contents)
    else:
        return None


def saveJson(dataDict: dict, jsonPath: str | Path):
    if not isinstance(jsonPath, Path):
        jsonPath = Path(jsonPath)
    if not jsonPath.parent.is_dir():
        os.makedirs(jsonPath.parent)
    with open(jsonPath, "w") as file:
        file.write(json.dumps(dataDict, indent=4))


def downloadFileFromUrl(url: str, location: Path):
    r = requests.get(url)
    open(location.as_posix(), 'wb').write(r.content)


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


class counter(object):
    """counter
    from : https://stackoverflow.com/questions/1485841/behaviour-of-increment-and-decrement-operators-in-python
    """
    def __init__(self, v=0):
        self.set(v)

    def preinc(self):
        self.v += 1
        return self.v

    def predec(self):
        self.v -= 1
        return self.v

    def postinc(self):
        self.v += 1
        return self.v - 1

    def postdec(self):
        self.v -= 1
        return self.v + 1

    def val(self):
        return self.v

    def __add__(self, addend):
        return self.v + addend

    def __sub__(self, subtrahend):
        return self.v - subtrahend

    def __mul__(self, multiplier):
        return self.v * multiplier

    def __div__(self, divisor):
        return self.v / divisor

    def __getitem__(self):
        return self.v

    def __str__(self):
        return str(self.v)

    def set(self, v):
        if not isinstance(v, int):
            v = 0
        self.v = v


# --------------------------------- MTG stuff -------------------------------- #

def getColor(coloridentity: str) -> tuple:
    BASICCOLORS = {
        "W": (249, 250, 244),
        "U": (14, 104, 171),
        "B": (21, 11, 0),
        "R": (211, 32, 42),
        "G": (0, 115, 62)
    }
    r = []
    g = []
    b = []
    if coloridentity != "":
        colors = list(coloridentity)
        for color in colors:
            r.append(BASICCOLORS[color][0])
            g.append(BASICCOLORS[color][1])
            b.append(BASICCOLORS[color][2])
        r = int(sum(r) / len(r))
        g = int(sum(g) / len(g))
        b = int(sum(b) / len(b))

        return (r, g, b)
    else:
        return (128, 128, 128)


def setManaText(inputStr) -> str:
    # NDPMTG / Proxyglyph
    for k, v in PROXYGLYPH_SYMBOLS.items():
        inputStr = inputStr.replace(k, v)
    # remove plain circle background symbols, not needed
    inputStr = inputStr.replace("Q", "").replace("o", "").replace("q", "")
    return inputStr


def setSetsText(sets: list):
    KEYRUNE_EQU_PATH = constants.DEFAULT_FONTS_LOCATION / "keyrune.json"
    KEYRUNE_SYMBOLS = loadJson(KEYRUNE_EQU_PATH)
    setsStr = ""
    for set in sets:
        if getFromDict(KEYRUNE_SYMBOLS, [set]) is not None:
            setsStr += html.unescape(getFromDict(KEYRUNE_SYMBOLS, [set]))
    return setsStr


def updateKeyRuneSymbols():
    cheatSheetUrl = "https://raw.githubusercontent.com/andrewgioia/keyrune/master/docs/cheatsheet.html"
    cheatSheetHtml = requests.get(cheatSheetUrl).text
    soup = BeautifulSoup(cheatSheetHtml, 'html.parser')
    # equ. data liik like: <span class="utf"><i>&#xe60b;</i> ss-10e <code>&amp;#xe60b;</code></span>
    equDict = {}
    for equ in soup.find_all('span'):
        if equ.attrs["class"] == ["utf"]:
            set = str(equ.contents[1]).strip().replace("ss-", "")
            keyRuneCode = str(equ.contents[2]).replace("amp;", "").replace("<code>", "").replace("</code>", "")
            equDict.update({set: keyRuneCode})
    with open(constants.DEFAULT_FONTS_LOCATION / "keyrune.json", "w") as outfile:
        outfile.write(json.dumps(equDict, indent=4))


def updateManaFontSymbols():
    ...


# -------------------------------- Font equiv -------------------------------- #

# Dictionary of symbols as they appear in oracle text, and their corresponding symbols to look correct in NDPMTG font
# From https://github.com/MrTeferi/Proxyshop/blob/main/src/constants.py
PROXYGLYPH_SYMBOLS = {
    "{W/P}": "Qp",
    "{U/P}": "Qp",
    "{B/P}": "Qp",
    "{R/P}": "Qp",
    "{G/P}": "Qp",
    "{W/U/P}": "Qqyz",
    "{U/B/P}": "Qqyz",
    "{B/R/P}": "Qqyz",
    "{R/G/P}": "Qqyz",
    "{G/W/P}": "Qqyz",
    "{W/B/P}": "Qqyz",
    "{B/G/P}": "Qqyz",
    "{G/U/P}": "Qqyz",
    "{U/R/P}": "Qqyz",
    "{R/W/P}": "Qqyz",
    "{A}": "oi",
    "{E}": "e",
    "{T}": "ot",
    "{X}": "ox",
    "{Y}": "oY",
    "{Z}": "oZ",
    "{∞}": "o∞",
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
    "{17}": "oÅ",
    "{18}": "oÆ",
    "{19}": "oÃ",
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
    "{CHAOS}": "?",
    "{1000000}": "10000000"  # Gleemax exception, since symbol not available / not pretty
}
