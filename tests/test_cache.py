import constants
import connector
import widgets.settings as settings
from PySide6 import QtWidgets


def test_clear_cache_removes_only_cache_files(tmp_path, monkeypatch):
    cacheDb = tmp_path / "mtg_org_cache.db"
    cacheDb.write_text("cache")
    infos = tmp_path / "infos"
    infos.mkdir()
    (infos / "sets.json").write_text("{}")
    images = tmp_path / "card_imgs"
    images.mkdir()
    (images / "card-1").write_bytes(b"image")
    (images / "card-2").write_bytes(b"img")
    icons = tmp_path / "sets_icons"
    icons.mkdir()
    (icons / "set.svg").write_text("<svg/>")
    bulk = tmp_path / "bulk"
    bulk.mkdir()
    (bulk / "default-cards-cache.sqlite3").write_text("db")
    (bulk / "default-cards-20240101000000.jsonl.gz").write_text("bulk")
    userDb = tmp_path / "mtg_org.db"
    userDb.write_text("decks")

    monkeypatch.setattr(constants, "DEFAULT_CACHE_DB_LOCATION", cacheDb)
    monkeypatch.setattr(constants, "DEFAULT_INFOS_LOCATION", infos)
    monkeypatch.setattr(constants, "DEFAULT_CARDIMAGES_LOCATION", images)
    monkeypatch.setattr(constants, "DEFAULT_SET_ICONS_LOCATION", icons)
    monkeypatch.setattr(constants, "DEFAULT_BULK_FOLDER_LOCATION", bulk)

    stats = connector.clearCache()

    assert not cacheDb.exists()
    assert not (infos / "sets.json").exists()
    assert list(images.iterdir()) == []
    assert list(icons.iterdir()) == []
    assert not (bulk / "default-cards-cache.sqlite3").exists()
    assert (bulk / "default-cards-20240101000000.jsonl.gz").exists()
    assert userDb.read_text() == "decks"
    assert stats["files"] == 6
    assert stats["bytes"] == 5 + 2 + 5 + 3 + 6 + 2
    assert stats["errors"] == []


def test_settings_clear_cache_button(qtApp, monkeypatch):
    calls = []
    monkeypatch.setattr(
        settings.connector,
        "clearCache",
        lambda: calls.append(True) or {"files": 2, "bytes": 2048, "errors": []},
    )
    monkeypatch.setattr(settings.scryfall, "resetSetsCache", lambda: None)
    monkeypatch.setattr(settings.scryfall, "resetFormatsCache", lambda: None)
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "question",
        lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *args, **kwargs: None)

    dialog = settings.SettingsDialog()
    dialog.on_clearCacheClicked()

    assert calls == [True]


def test_get_storage_stats(tmp_path, monkeypatch):
    userDb = tmp_path / "mtg_org.db"
    userDb.write_bytes(b"decks")
    cardCache = tmp_path / "mtg_org_cache.db"
    cardCache.write_bytes(b"cache")
    images = tmp_path / "card_imgs"
    images.mkdir()
    (images / "card-1").write_bytes(b"image")
    icons = tmp_path / "sets_icons"
    icons.mkdir()
    (icons / "set.svg").write_bytes(b"<svg/>")
    infos = tmp_path / "infos"
    infos.mkdir()
    (infos / "sets.json").write_bytes(b"{}")
    bulk = tmp_path / "bulk"
    bulk.mkdir()
    (bulk / "default-cards-20240101000000.jsonl.gz").write_bytes(b"bulk-data")
    (bulk / "default-cards-cache.sqlite3").write_bytes(b"sqlite-index")

    monkeypatch.setattr(constants, "DEFAULT_DB_LOCATION", userDb)
    monkeypatch.setattr(constants, "DEFAULT_CACHE_DB_LOCATION", cardCache)
    monkeypatch.setattr(constants, "DEFAULT_CARDIMAGES_LOCATION", images)
    monkeypatch.setattr(constants, "DEFAULT_SET_ICONS_LOCATION", icons)
    monkeypatch.setattr(constants, "DEFAULT_INFOS_LOCATION", infos)
    monkeypatch.setattr(constants, "DEFAULT_BULK_FOLDER_LOCATION", bulk)

    stats = connector.getStorageStats()

    assert stats == {
        "decks": 5,
        "card_cache": 5,
        "images": 5,
        "set_icons": 6,
        "set_metadata": 2,
        "bulk_files": 9,
        "bulk_index": 12,
    }


def test_settings_shows_storage_sizes(qtApp, monkeypatch):
    monkeypatch.setattr(
        settings.connector,
        "getStorageStats",
        lambda: {
            "decks": 0,
            "card_cache": 1024,
            "images": 2048,
            "set_icons": 0,
            "set_metadata": 0,
            "bulk_files": 1024 * 1024,
            "bulk_index": 1024 * 1024 * 1024,
        },
    )
    dialog = settings.SettingsDialog()

    assert dialog.resultLimitCB.currentData() == 100
    assert dialog.storageLabels["decks"].text() == "0 B"
    assert dialog.storageLabels["card_cache"].text() == "1.0 KB"
    assert dialog.storageLabels["images"].text() == "2.0 KB"
    assert dialog.storageLabels["bulk_files"].text() == "1.0 MB"
    assert dialog.storageLabels["bulk_index"].text() == "1.0 GB"


def test_ensure_bulk_cache_with_progress(qtApp, monkeypatch):
    calls = []

    def fakeEnsure(progress_callback=None):
        progress_callback(10)
        calls.append(True)
        return 10

    monkeypatch.setattr(settings.scryfall, "ensureBulkDataReady", fakeEnsure)

    assert settings.ensureBulkCacheWithProgress(None) is True
    assert calls == [True]
