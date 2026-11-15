import config
import constants
from PySide6 import QtWidgets
from widgets import settings


def test_settings_dialog_saves_theme(qtApp, tmp_path, monkeypatch):
    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    monkeypatch.setattr(constants, "THEME", "fusion")
    config.createConfigFile()
    messages = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "information",
        lambda *args, **kwargs: messages.append(args[1]),
    )

    dialog = settings.SettingsDialog()
    assert dialog.themeCB.currentData() == "fusion"
    dialog.themeCB.setCurrentIndex(dialog.themeCB.findData("material"))
    dialog.accept()

    assert config.getUISettings() == {"theme": "material"}
    assert messages == ["Theme changed"]


def test_settings_dialog_applies_theme_live(qtApp, tmp_path, monkeypatch):
    class Parent(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.applied = 0

        def applyTheme(self):
            self.applied += 1

    configPath = tmp_path / "settings.ini"
    monkeypatch.setattr(constants, "DEFAULT_CONFIGURATION_FILE", configPath)
    monkeypatch.setattr(constants, "THEME", "fusion")
    config.createConfigFile()
    parent = Parent()
    dialog = settings.SettingsDialog(parent)
    dialog.themeCB.setCurrentIndex(dialog.themeCB.findData("material"))

    dialog.accept()

    assert parent.applied == 1


def test_deck_selector_settings_button_has_icon(qtApp):
    from widgets import deckselector

    selector = deckselector.CardStackSelector()

    assert not selector.settingsPB.icon().isNull()
