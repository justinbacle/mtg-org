import datetime

import config
import constants
from lib import updates


def test_version_comparison():
    assert updates.isNewer("v0.1.42", "0.1.41")
    assert not updates.isNewer("v0.1.41", "0.1.41")
    assert updates.isNewer("v0.1.42", "0.1.dev")


def test_update_check_uses_release_and_skips_version(tmp_path, monkeypatch):
    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    monkeypatch.setattr(constants, "AUTO_CHECK_UPDATES", True)
    config.createConfigFile()
    config.saveUpdateSettings(True, skippedVersion="")
    monkeypatch.setattr(updates.constants, "appVersion", lambda: "0.1.1")

    class Response:
        status_code = 200

        def json(self):
            return {
                "tag_name": "v0.1.2",
                "html_url": "https://example.test/release",
                "body": "notes",
            }

    monkeypatch.setattr(updates.requests, "get", lambda *args, **kwargs: Response())

    result = updates.checkForUpdate(force=True)
    assert result == {
        "version": "v0.1.2",
        "url": "https://example.test/release",
        "body": "notes",
    }

    config.saveUpdateSettings(True, skippedVersion="v0.1.2")
    assert updates.checkForUpdate(force=True) is None


def test_update_check_is_throttled(tmp_path, monkeypatch):
    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    config.createConfigFile()
    config.saveUpdateSettings(True)
    config.saveUpdateCheck(datetime.datetime.now().strftime(constants.DATETIME_FORMAT))
    called = []
    monkeypatch.setattr(updates.requests, "get", lambda *args, **kwargs: called.append(True))

    assert updates.checkForUpdate() is None
    assert called == []
