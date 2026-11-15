import json
import os
import time

import pytest

import constants
from lib import utils


def writeKeyRune(fonts, data, ageSeconds=0):
    fonts.mkdir(parents=True, exist_ok=True)
    path = fonts / "keyrune.json"
    path.write_text(json.dumps(data))
    if ageSeconds:
        oldTime = time.time() - ageSeconds
        os.utime(path, (oldTime, oldTime))
    return path


def test_find_missing_keyrune_sets(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", tmp_path)
    writeKeyRune(tmp_path, {"2ed": "&#xe602;"})
    assert utils.findMissingKeyRuneSets(["2ed", "slc", "ced"]) == ["ced", "slc"]


def test_keyrune_update_due_uses_file_age(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", tmp_path)
    path = writeKeyRune(tmp_path, {}, ageSeconds=2 * 24 * 60 * 60)
    assert utils.keyRuneUpdateDue() is True
    now = time.time()
    os.utime(path, (now, now))
    assert utils.keyRuneUpdateDue() is False


def test_missing_keyrune_set_triggers_update(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", tmp_path)
    writeKeyRune(tmp_path, {"2ed": "&#xe602;"}, ageSeconds=2 * 24 * 60 * 60)
    calls = []

    def fakeUpdateSymbols():
        writeKeyRune(tmp_path, {"2ed": "&#xe602;", "slc": "&#xe999;"})
        calls.append("symbols")

    def fakeDownload(url, path):
        calls.append("font")
        path.write_text("font")

    monkeypatch.setattr(utils, "updateKeyRuneSymbols", fakeUpdateSymbols)
    monkeypatch.setattr(utils, "downloadFileFromUrl", fakeDownload)

    assert utils.updateKeyRuneIfMissing(["2ed", "slc"]) == []
    assert calls == ["symbols", "font"]


def test_recent_keyrune_is_not_refreshed(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", tmp_path)
    writeKeyRune(tmp_path, {"2ed": "&#xe602;"})
    monkeypatch.setattr(utils, "updateKeyRuneSymbols", lambda: pytest.fail("should not refresh"))

    assert utils.updateKeyRuneIfMissing(["2ed", "slc"]) == ["slc"]


def test_font_not_downloaded_when_keyrune_still_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_FONTS_LOCATION", tmp_path)
    writeKeyRune(tmp_path, {"2ed": "&#xe602;"}, ageSeconds=2 * 24 * 60 * 60)
    calls = []

    def fakeUpdateSymbols():
        writeKeyRune(tmp_path, {"2ed": "&#xe602;"})
        calls.append("symbols")

    def fakeDownload(url, path):
        calls.append("font")

    monkeypatch.setattr(utils, "updateKeyRuneSymbols", fakeUpdateSymbols)
    monkeypatch.setattr(utils, "downloadFileFromUrl", fakeDownload)

    assert utils.updateKeyRuneIfMissing(["2ed", "slc"]) == ["slc"]
    assert calls == ["symbols"]
