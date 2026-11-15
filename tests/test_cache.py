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
    userDb = tmp_path / "mtg_org.db"
    userDb.write_text("decks")

    monkeypatch.setattr(constants, "DEFAULT_CACHE_DB_LOCATION", cacheDb)
    monkeypatch.setattr(constants, "DEFAULT_INFOS_LOCATION", infos)
    monkeypatch.setattr(constants, "DEFAULT_CARDIMAGES_LOCATION", images)
    monkeypatch.setattr(constants, "DEFAULT_SET_ICONS_LOCATION", icons)

    stats = connector.clearCache()

    assert not cacheDb.exists()
    assert not (infos / "sets.json").exists()
    assert list(images.iterdir()) == []
    assert list(icons.iterdir()) == []
    assert userDb.read_text() == "decks"
    assert stats["files"] == 5
    assert stats["bytes"] == 5 + 2 + 5 + 3 + 6
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
