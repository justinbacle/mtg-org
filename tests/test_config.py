import config
import constants


def test_scryfall_settings_defaults_and_roundtrip(tmp_path, monkeypatch):
    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    monkeypatch.setattr(constants, "USE_BULK_FILES", False)
    monkeypatch.setattr(constants, "BULK_AUTO_UPDATE", True)
    monkeypatch.setattr(constants, "BULK_LANGUAGE_MODE", "english")

    config.createConfigFile()
    assert config.getScryfallSettings() == {
        "use_bulk_files": False,
        "bulk_auto_update": True,
        "bulk_language_mode": "english",
    }

    config.saveScryfallSettings(True, False, "all")
    assert config.getScryfallSettings() == {
        "use_bulk_files": True,
        "bulk_auto_update": False,
        "bulk_language_mode": "all",
    }

    config.loadScryfallSettings()
    assert constants.USE_BULK_FILES is True
    assert constants.BULK_AUTO_UPDATE is False
    assert constants.BULK_LANGUAGE_MODE == "all"


def test_invalid_bulk_language_mode_falls_back_to_english(tmp_path, monkeypatch):
    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    config.createConfigFile()
    config.writeValue("invalid", "SCRYFALL", "bulk_language_mode")
    assert config.getScryfallSettings()["bulk_language_mode"] == "english"


def test_search_result_limit_roundtrip(tmp_path, monkeypatch):
    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    monkeypatch.setattr(constants, "SEARCH_RESULT_LIMIT", 100)
    config.createConfigFile()

    assert config.getSearchSettings() == {"result_limit": 100}

    config.saveSearchSettings(250)
    assert config.getSearchSettings() == {"result_limit": 250}

    config.loadSearchSettings()
    assert constants.SEARCH_RESULT_LIMIT == 250
