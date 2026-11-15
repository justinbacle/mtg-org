import pytest

from lib import cachestate, datarefresh, scryfall, utils


def test_new_set_codes_detects_released_missing_set():
    remote = [
        {"code": "old", "released_at": "2020-01-01"},
        {"code": "new", "released_at": "2024-06-01"},
    ]
    cached = [{"code": "old"}]

    assert datarefresh.newSetCodes(remote, cached, today="2024-06-02") == ["new"]


def test_new_set_codes_ignores_unreleased_set():
    remote = [{"code": "future", "released_at": "2024-07-01"}]

    assert datarefresh.newSetCodes(remote, [], today="2024-06-02") == []


def test_sets_fingerprint_changes_for_released_set_only():
    old = [{"code": "old", "name": "Old", "released_at": "2020-01-01"}]
    new = old + [{"code": "new", "name": "New", "released_at": "2024-06-01"}]
    future = old + [{"code": "future", "name": "Future", "released_at": "2024-07-01"}]

    assert datarefresh.setsFingerprint(old, today="2024-06-02") != datarefresh.setsFingerprint(
        new, today="2024-06-02"
    )
    assert datarefresh.setsFingerprint(old, today="2024-06-02") == datarefresh.setsFingerprint(
        future, today="2024-06-02"
    )


def test_check_for_updates_bumps_generation_once(tmp_path, monkeypatch):
    setsPath = tmp_path / "sets.json"
    utils.saveJson(
        {"sets": [{"code": "old", "name": "Old", "released_at": "2020-01-01"}]},
        setsPath,
    )
    remote = {"sets": [
        {"code": "old", "name": "Old", "released_at": "2020-01-01"},
        {"code": "new", "name": "New", "released_at": "2024-06-01"},
    ]}
    calls = []

    monkeypatch.setattr(datarefresh.constants, "USE_BULK_FILES", False)
    monkeypatch.setattr(datarefresh.constants, "DEFAULT_INFOS_LOCATION", tmp_path)
    monkeypatch.setattr(datarefresh.scryfall, "getOnlineSetData", lambda: remote)
    monkeypatch.setattr(datarefresh.scryfall, "resetDataCaches", lambda: calls.append("reset"))
    monkeypatch.setattr(datarefresh.connector, "pruneOldCards", lambda: calls.append("prune"))
    monkeypatch.setattr(utils, "updateKeyRuneIfMissing", lambda codes: calls.append(("keyrune", codes)))

    first = datarefresh.checkForUpdates()
    second = datarefresh.checkForUpdates()

    assert first.updated is True
    assert first.new_sets == ("new",)
    assert second.updated is False
    assert cachestate.getCardGeneration() == 2
    assert utils.loadJson(setsPath) == remote
    assert calls == ["prune", "reset", ("keyrune", ["new"])]


@pytest.mark.real_scryfall
def test_get_sets_is_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(scryfall.constants, "USE_BULK_FILES", False)
    monkeypatch.setattr(scryfall.constants, "DEFAULT_INFOS_LOCATION", tmp_path)
    monkeypatch.setattr(scryfall, "_sets_memory_cache", None)

    assert scryfall.getSets() == []
