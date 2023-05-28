import requests
import functools
import operator
from dotmap import DotMap
import re
import json
import html


def getUrlData(url):
    if url is not None:
        r = requests.get(url)
        return r.text


def getUrlJsonData(url):
    text = getUrlData(url)
    jsonData = json.loads(text)
    return jsonData


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


def setSetsText(sets: list):
    setsStr = ""
    for set in sets:
        if getFromDict(KEYRUNE_SYMBOLS, [set]) is not None:
            setsStr += html.unescape(getFromDict(KEYRUNE_SYMBOLS, [set]))
    return setsStr


# -------------------------------- Font equiv -------------------------------- #

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

KEYRUNE_SYMBOLS = {
    "10e": "&#xe60b;",
    "1e": "&#xe947;",
    "2e": "&#xe948;",
    "2ed": "&#xe602;",
    "2u": "&#xe949;",
    "2xm": "&#xe96e;",
    "2x2": "&#xe99c;",
    "30a": "&#xe9aa;",
    "3e": "&#xe94a;",
    "3ed": "&#xe603;",
    "40k": "&#xe998;",
    "4ed": "&#xe604;",
    "5dn": "&#xe633;",
    "5ed": "&#xe606;",
    "6ed": "&#xe607;",
    "7ed": "&#xe608;",
    "8ed": "&#xe609;",
    "9ed": "&#xe60a;",
    "a25": "&#xe93d;",
    "aer": "&#xe90f;",
    "afc": "&#xe981;",
    "afr": "&#xe972;",
    "akh": "&#xe914;",
    "akr": "&#xe970;",
    "ala": "&#xe641;",
    "all": "&#xe61a;",
    "ann": "&#xe92d;",
    "apc": "&#xe62a;",
    "arb": "&#xe643;",
    "arc": "&#xe657;",
    "arn": "&#xe613;",
    "ath": "&#xe65f;",
    "atq": "&#xe614;",
    "avr": "&#xe64c;",
    "bbd": "&#xe942;",
    "bfz": "&#xe699;",
    "bng": "&#xe651;",
    "bok": "&#xe635;",
    "bot": "&#xe99e;",
    "brb": "&#xe660;",
    "brc": "&#xe99f;",
    "bro": "&#xe99d;",
    "brr": "&#xe9a0;",
    "btd": "&#xe661;",
    "c13": "&#xe65b;",
    "c14": "&#xe65d;",
    "c15": "&#xe900;",
    "c16": "&#xe910;",
    "c17": "&#xe934;",
    "c18": "&#xe946;",
    "c19": "&#xe95f;",
    "c20": "&#xe966;",
    "c21": "&#xe97e;",
    "clb": "&#xe991;",
    "cc1": "&#xe968;",
    "cc2": "&#xe987;",
    "chk": "&#xe634;",
    "chr": "&#xe65e;",
    "cm1": "&#xe65a;",
    "cm2": "&#xe940;",
    "cma": "&#xe916;",
    "cmc": "&#xe969;",
    "cmd": "&#xe658;",
    "cmr": "&#xe969;",
    "cns": "&#xe65c;",
    "cn2": "&#xe904;",
    "con": "&#xe642;",
    "csp": "&#xe61b;",
    "dd2": "&#xe66a;",
    "ddc": "&#xe66b;",
    "ddd": "&#xe66c;",
    "dde": "&#xe66d;",
    "ddf": "&#xe66e;",
    "ddg": "&#xe66f;",
    "ddh": "&#xe670;",
    "ddi": "&#xe671;",
    "ddj": "&#xe672;",
    "ddk": "&#xe673;",
    "ddl": "&#xe674;",
    "ddm": "&#xe675;",
    "ddn": "&#xe676;",
    "ddo": "&#xe677;",
    "ddp": "&#xe698;",
    "ddq": "&#xe908;",
    "ddr": "&#xe90d;",
    "dds": "&#xe921;",
    "ddt": "&#xe933;",
    "ddu": "&#xe93e;",
    "dgm": "&#xe64f;",
    "dis": "&#xe639;",
    "dka": "&#xe64b;",
    "dkm": "&#xe662;",
    "dmr": "&#xe9a4;",
    "dmu": "&#xe993;",
    "dmc": "&#xe994;",
    "dom": "&#xe93f;",
    "dpa": "&#xe689;",
    "drb": "&#xe678;",
    "drk": "&#xe616;",
    "dst": "&#xe632;",
    "dtk": "&#xe693;",
    "e01": "&#xe92d;",
    "e02": "&#xe931;",
    "ea1": "&#xe9b4;",
    "eld": "&#xe95e;",
    "ema": "&#xe903;",
    "emn": "&#xe90b;",
    "eve": "&#xe640;",
    "evg": "&#xe669;",
    "exo": "&#xe621;",
    "exp": "&#xe69a;",
    "fem": "&#xe617;",
    "frf": "&#xe654;",
    "fut": "&#xe63c;",
    "gk1": "&#xe94b;",
    "gk2": "&#xe959;",
    "gn2": "&#xe964;",
    "gn3": "&#xe9a5;",
    "gnt": "&#xe94d;",
    "gpt": "&#xe638;",
    "grn": "&#xe94b;",
    "gs1": "&#xe945;",
    "gtc": "&#xe64e;",
    "h09": "&#xe67f;",
    "h17": "&#xe938;",
    "ha1": "&#xe96b;",
    "hbg": "&#xe9a6;",
    "hml": "&#xe618;",
    "hop": "&#xe656;",
    "hou": "&#xe924;",
    "ice": "&#xe619;",
    "ice2": "&#xe925;",
    "iko":"&ampe962;",
    "ima": "&#xe935;",
    "inv": "&#xe628;",
    "isd": "&#xe64a;",
    "j20": "&#xe96a;",
    "j21": "&#xe983;",
    "j22": "&#xe9ad;",
    "jmp": "&#xe96f;",
    "jou": "&#xe652;",
    "jud": "&#xe62d;",
    "khc": "&#xe97d;",
    "khm": "&#xe974;",
    "kld": "&#xe90e;",
    "klr": "&#xe97c;",
    "ktk": "&#xe653;",
    "lea": "&#xe600;",
    "leb": "&#xe601;",
    "leg": "&#xe615;",
    "lgn": "&#xe62f;",
    "lrw": "&#xe63d;",
    "ltc": "&#xe9b6;",
    "ltr": "&#xe9af;",
    "m10": "&#xe60c;",
    "m11": "&#xe60d;",
    "m12": "&#xe60e;",
    "m13": "&#xe60f;",
    "m14": "&#xe610;",
    "m15": "&#xe611;",
    "m19": "&#xe941;",
    "m20": "&#xe95d;",
    "m21": "&#xe960;",
    "mat": "&#xe9a3;",
    "mb1": "&#xe971;",
    "mbs": "&#xe648;",
    "md1": "&#xe682;",
    "me1": "&#xe68d;",
    "me2": "&#xe68e;",
    "me3": "&#xe68f;",
    "me4": "&#xe690;",
    "med": "&#xe94c;",
    "mh1": "&#xe95b;",
    "mh2": "&#xe97b;",
    "mic": "&#xe985;",
    "mid": "&#xe978;",
    "mir": "&#xe61c;",
    "mm2": "&#xe695;",
    "mm3": "&#xe912;",
    "mma": "&#xe663;",
    "mmq": "&#xe625;",
    "moc": "&#xe9a9;",
    "mom": "&#xe9a2;",
    "mor": "&#xe63e;",
    "mp1": "&#xe913;",
    "mp2": "&#xe922;",
    "mps": "&#xe913;",
    "mrd": "&#xe631;",
    "mul": "&#xe9ba;",
    "nem": "&#xe626;",
    "nec": "&#xe98d;",
    "neo": "&#xe98c;",
    "nms": "&#xe626;",
    "ncc": "&#xe98e;",
    "nph": "&#xe649;",
    "ody": "&#xe62b;",
    "ogw": "&#xe901;",
    "onc": "&#xe9a8;",
    "one": "&#xe9a1;",
    "ons": "&#xe62e;",
    "ori": "&#xe697;",
    "p02": "&#xe665;",
    "pc2": "&#xe659;",
    "pca": "&#xe911;",
    "pcy": "&#xe627;",
    "pd2": "&#xe680;",
    "pd3": "&#xe681;",
    "plc": "&#xe63b;",
    "pls": "&#xe629;",
    "po2": "&#xe665;",
    "por": "&#xe664;",
    "ptg": "&#xe965;",
    "ptk": "&#xe666;",
    "rav": "&#xe637;",
    "rix": "&#xe92f;",
    "xren": "&#xe917;",
    "xrin":"&ampe918;",
    "rna":"&ampe959;",
    "roe": "&#xe646;",
    "rtr": "&#xe64d;",
    "s00": "&#xe668;",
    "s99": "&#xe667;",
    "scd": "&#xe9ab;",
    "scg": "&#xe630;",
    "shm": "&#xe63f;",
    "sir": "&#xe9b1;",
    "sis": "&#xe9b2;",
    "sld": "&#xe687;",
    "slu": "&#xe687;",
    "snc": "&#xe98b;",
    "soi": "&#xe902;",
    "sok": "&#xe636;",
    "som": "&#xe647;",
    "ss1": "&#xe944;",
    "ss2": "&#xe95c;",
    "ss3": "&#xe96d;",
    "sta": "&#xe980;",
    "sth": "&#xe620;",
    "stx": "&#xe975;",
    "td2": "&#xe91c;",
    "thb": "&#xe961;",
    "ths": "&#xe650;",
    "tmp": "&#xe61f;",
    "tor": "&#xe62c;",
    "tpr": "&#xe694;",
    "tsp": "&#xe63a;",
    "tsr": "&#xe976;",
    "uds": "&#xe624;",
    "ugl": "&#xe691;",
    "ulg": "&#xe623;",
    "uma": "&#xe958;",
    "und": "&#xe96c;",
    "unf": "&#xe98a;",
    "unh": "&#xe692;",
    "ust": "&#xe930;",
    "usg": "&#xe622;",
    "v09": "&#xe679;",
    "v0x": "&#xe920;",
    "v10": "&#xe67a;",
    "v11": "&#xe67b;",
    "v12": "&#xe67c;",
    "v13": "&#xe67d;",
    "v14": "&#xe67e;",
    "v15": "&#xe905;",
    "v16": "&#xe906;",
    "v17": "&#xe939;",
    "van": "&#xe655;",
    "vis": "&#xe61d;",
    "voc": "&#xe986;",
    "vow": "&#xe977;",
    "vma": "&#xe696;",
    "w16": "&#xe907;",
    "w17": "&#xe923;",
    "war": "&#xe95a;",
    "who": "&#xe9b0;",
    "woe": "&#xe9ae;",
    "woc": "&#xe9b9;",
    "wth": "&#xe61e;",
    "wwk": "&#xe645;",
    "xln": "&#xe92e;",
    "y22": "&#xe989;",
    "ydmu": "&#xe9a7;",
    "zen":"&ampe644;",
    "znc": "&#xe967;",
    "znr": "&#xe963;"
}
