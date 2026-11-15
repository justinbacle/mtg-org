from PySide6 import QtCore, QtGui

import constants
from widgets import cardviewer


def test_cached_single_face_image_is_loaded(monkeypatch):
    monkeypatch.setattr(cardviewer, "isCardImageCached", lambda cardId: True)
    monkeypatch.setattr(constants, "IMG_DOWNLOAD_METHOD", "qt")
    monkeypatch.setattr(constants, "USE_BULK_FILES", True)
    assert cardviewer.getCardImageAction("card-id", "https://img", hasManyFaces=False) == "load"


def test_bulk_mode_downloads_missing_image(monkeypatch):
    monkeypatch.setattr(cardviewer, "isCardImageCached", lambda cardId: False)
    monkeypatch.setattr(constants, "IMG_DOWNLOAD_METHOD", "qt")
    monkeypatch.setattr(constants, "USE_BULK_FILES", True)
    assert cardviewer.getCardImageAction("card-id", "https://img", hasManyFaces=False) == "download"


def test_missing_image_uri_does_nothing(monkeypatch):
    monkeypatch.setattr(cardviewer, "isCardImageCached", lambda cardId: False)
    monkeypatch.setattr(constants, "IMG_DOWNLOAD_METHOD", "qt")
    assert cardviewer.getCardImageAction("card-id", None, hasManyFaces=False) == "none"


def test_direct_mode_does_not_load_a_missing_file(monkeypatch):
    monkeypatch.setattr(cardviewer, "isCardImageCached", lambda cardId: False)
    monkeypatch.setattr(constants, "IMG_DOWNLOAD_METHOD", "direct")
    assert cardviewer.getCardImageAction("card-id", "https://img", hasManyFaces=False) == "none"


def test_printing_selector_is_connected_once(qtApp, monkeypatch):
    calls = []

    class CountingViewer(cardviewer.CardViewer):
        def on_printingChange(self):
            calls.append(True)

    viewer = CountingViewer()
    viewer.setManaFont = lambda: None
    viewer.downloadCardImg = lambda imageUri, cardId: None
    monkeypatch.setattr(cardviewer, "isCardImageCached", lambda cardId: False)

    data = {
        "card": {
            "id": "card-id",
            "name": "Test Card",
            "lang": "en",
            "mana_cost": "{1}",
            "rarity": "common",
            "set": "tst",
            "type_line": "Instant",
            "oracle_text": "Test text.",
            "scryfall_uri": "https://scryfall.com/card/test",
            "prices": {},
            "image_uris": {"large": "https://img"},
        },
        "cardFace": 0,
        "printings": [
            {"id": "card-id", "set": "tst", "set_name": "Test Set", "collector_number": "1"},
            {"id": "card-id-2", "set": "tst2", "set_name": "Other Set", "collector_number": "2"},
        ],
        "setIconSvgData": None,
        "forceRefresh": False,
    }

    viewer._on_display_data_ready(data)
    viewer._on_display_data_ready(data)
    viewer.printingSelect.setCurrentIndex(1)

    assert len(calls) == 1


def test_save_image_makes_it_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_CARDIMAGES_LOCATION", tmp_path)
    monkeypatch.setattr(constants, "IMG_DOWNLOAD_METHOD", "qt")
    image = QtGui.QImage(8, 8, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("red"))

    cardviewer.saveCardImg(image, "card-id")

    assert cardviewer.isCardImageCached("card-id")
    assert cardviewer.getCardImageAction("card-id", "https://img") == "load"


def test_image_downloader_decodes_local_image(qtApp, tmp_path):
    image = QtGui.QImage(4, 4, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("red"))
    imagePath = tmp_path / "card.png"
    assert image.save(imagePath.as_posix())

    downloader = cardviewer.ImageDownloader()
    result = {}
    loop = QtCore.QEventLoop()

    def onFinished(downloadedImage, cardId):
        result["image"] = downloadedImage
        result["cardId"] = cardId
        loop.quit()

    downloader.finished.connect(onFinished)
    QtCore.QTimer.singleShot(5000, loop.quit)
    downloader.start_download(QtCore.QUrl.fromLocalFile(imagePath.as_posix()), "card-id")
    loop.exec()

    assert result["cardId"] == "card-id"
    assert not result["image"].isNull()
    assert result["image"].width() == 4


def test_printing_label_describes_variants():
    regular = cardviewer.getPrintingLabel({
        "set": "fra",
        "set_name": "Reality Fracture",
        "collector_number": "128",
        "frame_effects": ["legendary"],
        "finishes": ["nonfoil", "foil"],
    })
    showcase = cardviewer.getPrintingLabel({
        "set": "fra",
        "set_name": "Reality Fracture",
        "collector_number": "418",
        "frame_effects": ["legendary", "showcase", "inverted"],
        "promo_types": ["fracturefoil"],
        "finishes": ["foil"],
    })

    assert regular.endswith(" - regular")
    assert "#418" in showcase
    assert "showcase" in showcase
    assert "foil only" in showcase


def test_viewer_minimum_width_independent_of_text(qtApp, monkeypatch):
    viewer = cardviewer.CardViewer()
    viewer.setManaFont = lambda: None
    viewer.downloadCardImg = lambda imageUri, cardId: None
    monkeypatch.setattr(cardviewer, "isCardImageCached", lambda cardId: False)

    def displayData(name, cardId, printings):
        return {
            "card": {
                "id": cardId,
                "name": name,
                "lang": "en",
                "mana_cost": "{1}",
                "rarity": "common",
                "set": "tst",
                "type_line": "Instant",
                "oracle_text": "Test text.",
                "scryfall_uri": "https://scryfall.com/card/test",
                "prices": {},
                "image_uris": {"large": "https://img"},
            },
            "cardFace": 0,
            "printings": printings,
            "setIconSvgData": None,
            "forceRefresh": False,
        }

    shortPrinting = {"id": "id-1", "set": "tst", "set_name": "Test Set", "collector_number": "1"}
    longPrinting = {
        "id": "id-2",
        "set": "fra",
        "set_name": "Reality Fracture With An Extremely Long Set Name For Testing",
        "collector_number": "418",
        "frame_effects": ["legendary", "showcase", "inverted"],
        "promo_types": ["fracturefoil", "japanshowcase"],
        "finishes": ["foil"],
    }

    viewer._on_display_data_ready(displayData("A", "id-1", [shortPrinting]))
    viewer.resize(500, 700)
    viewer.show()
    qtApp.processEvents()
    shortWidth = viewer.minimumSizeHint().width()
    assert viewer.nameLabel.width() > viewer.manacostLabel.width()

    viewer._on_display_data_ready(
        displayData(
            "A very very very long card name that should not widen the panel",
            "id-2",
            [longPrinting],
        )
    )
    qtApp.processEvents()

    assert viewer.minimumSizeHint().width() == shortWidth
