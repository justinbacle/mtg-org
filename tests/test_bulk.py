import gzip
import json
import time

import pytest
from PySide6 import QtWidgets

import constants
from lib import bulk, scryfall


pytestmark = pytest.mark.real_scryfall


SAMPLE_CARDS = [
    {
        "id": "bolt-old",
        "oracle_id": "oracle-bolt",
        "name": "Lightning Bolt",
        "set": "lea",
        "set_id": "set-lea",
        "set_name": "Limited Edition Alpha",
        "lang": "en",
        "released_at": "1993-08-05",
        "mtgo_id": 100,
        "colors": ["R"],
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "cmc": 1.0,
        "rarity": "common",
        "games": ["paper", "mtgo"],
        "legalities": {"modern": "legal", "legacy": "legal"},
        "prices": {"eur": "2.00"},
    },
    {
        "id": "bolt-new",
        "oracle_id": "oracle-bolt",
        "name": "Lightning Bolt",
        "set": "msc",
        "set_id": "set-msc",
        "set_name": "Modern Horizons 3 Commander",
        "lang": "en",
        "released_at": "2024-06-14",
        "mtgo_id": 200,
        "colors": ["R"],
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "cmc": 1.0,
        "rarity": "uncommon",
        "games": ["paper", "mtgo"],
        "legalities": {"modern": "legal", "legacy": "legal"},
        "prices": {"eur": "9.50"},
    },
    {
        "id": "bolt-fr",
        "oracle_id": "oracle-bolt",
        "name": "Foudre",
        "set": "lea",
        "set_id": "set-lea",
        "set_name": "Limited Edition Alpha",
        "lang": "fr",
        "released_at": "1993-08-05",
        "mtgo_id": 300,
        "colors": ["R"],
        "type_line": "Instant",
        "oracle_text": "Foudre inflige 3 blessures a n'importe quelle cible.",
        "cmc": 1.0,
        "rarity": "common",
        "games": ["paper"],
        "legalities": {"modern": "legal", "legacy": "legal"},
        "prices": {"eur": "1.50"},
    },
    {
        "id": "shock-new",
        "oracle_id": "oracle-shock",
        "name": "Shock",
        "set": "msc",
        "set_id": "set-msc",
        "set_name": "Modern Horizons 3 Commander",
        "lang": "en",
        "released_at": "2024-06-14",
        "mtgo_id": 400,
        "colors": ["R"],
        "type_line": "Instant",
        "oracle_text": "Shock deals 2 damage to any target.",
        "cmc": 1.0,
        "rarity": "common",
        "games": ["paper", "mtgo"],
        "legalities": {"modern": "legal", "legacy": "legal"},
        "prices": {"eur": "0.30"},
    },
]


for _sampleCard in SAMPLE_CARDS:
    _sampleCard.setdefault("mana_cost", "{1}")
    _sampleCard.setdefault("scryfall_uri", "https://scryfall.com/card/test")


@pytest.fixture
def bulkFolder(tmp_path, monkeypatch):
    folder = tmp_path / "bulk"
    folder.mkdir()
    (folder / "default-cards-20240101000000.json").write_text(
        json.dumps(SAMPLE_CARDS), encoding="utf-8"
    )
    monkeypatch.setattr(constants, "DEFAULT_BULK_FOLDER_LOCATION", folder)
    monkeypatch.setattr(constants, "USE_BULK_FILES", True)
    monkeypatch.setattr(constants, "BULK_LANGUAGE_MODE", "english")
    scryfall.resetBulkDataCache()
    scryfall.resetSetsCache()
    scryfall.resetFormatsCache()
    bulk.resetBulkInfoCache()
    yield folder
    scryfall.resetBulkDataCache()
    scryfall.resetSetsCache()
    scryfall.resetFormatsCache()
    bulk.resetBulkInfoCache()


def test_bulk_exact_search_returns_newest_first(bulkFolder):
    results = scryfall.searchCards({"name": "Lightning Bolt"}, exact=True)
    assert [card["id"] for card in results] == ["bolt-new", "bolt-old"]


def test_bulk_search_filters(bulkFolder):
    english = scryfall.searchCards({"name": "Lightning Bolt", "lang": "en"}, exact=True)
    assert {card["id"] for card in english} == {"bolt-new", "bolt-old"}

    bySet = scryfall.searchCards({"name": "Lightning Bolt", "set": "lea"}, exact=True)
    assert {card["id"] for card in bySet} == {"bolt-old"}

    byType = scryfall.searchCards({"name": "Shock", "types": ["instant"]}, exact=True)
    assert [card["id"] for card in byType] == ["shock-new"]

    byRarity = scryfall.searchCards({"name": "Lightning Bolt", "rarity": "uncommon"}, exact=True)
    assert [card["id"] for card in byRarity] == ["bolt-new"]

    byPrice = scryfall.searchCards({"name": "Lightning Bolt", "price": "eur<5"}, exact=True)
    assert {card["id"] for card in byPrice} == {"bolt-old"}

    byFormat = scryfall.searchCards({"name": "Shock", "f": "modern"}, exact=True)
    assert [card["id"] for card in byFormat] == ["shock-new"]


def test_exact_search_prefers_regular_nonfoil_printing(tmp_path, monkeypatch):
    cards = [
        {
            "id": "showcase-foil",
            "oracle_id": "oracle-denzilore",
            "name": "Denzilore Fatehold",
            "set": "fra",
            "set_id": "set-fra",
            "set_name": "Reality Fracture",
            "lang": "en",
            "released_at": "2026-10-02",
            "collector_number": "418",
            "frame_effects": ["legendary", "showcase", "inverted"],
            "promo_types": ["fracturefoil"],
            "finishes": ["foil"],
            "prices": {"eur_foil": "98.72"},
        },
        {
            "id": "regular",
            "oracle_id": "oracle-denzilore",
            "name": "Denzilore Fatehold",
            "set": "fra",
            "set_id": "set-fra",
            "set_name": "Reality Fracture",
            "lang": "en",
            "released_at": "2026-10-02",
            "collector_number": "128",
            "frame_effects": ["legendary"],
            "finishes": ["nonfoil", "foil"],
            "prices": {"eur": "2.47", "eur_foil": "3.01"},
        },
        {
            "id": "promo",
            "oracle_id": "oracle-denzilore",
            "name": "Denzilore Fatehold",
            "set": "pfra",
            "set_id": "set-pfra",
            "set_name": "Reality Fracture Promos",
            "lang": "en",
            "released_at": "2026-10-02",
            "collector_number": "128p",
            "frame_effects": ["legendary"],
            "promo_types": ["promopack", "stamped"],
            "finishes": ["nonfoil", "foil"],
            "prices": {"eur": "2.66", "eur_foil": "3.99"},
        },
    ]
    folder = tmp_path / "bulk"
    folder.mkdir()
    (folder / "default-cards-20240101000000.json").write_text(json.dumps(cards))
    monkeypatch.setattr(constants, "DEFAULT_BULK_FOLDER_LOCATION", folder)
    monkeypatch.setattr(constants, "USE_BULK_FILES", True)
    monkeypatch.setattr(constants, "BULK_LANGUAGE_MODE", "english")
    scryfall.resetBulkDataCache()
    scryfall.resetSetsCache()

    results = scryfall.searchCards({"name": "Denzilore Fatehold"}, exact=True)
    assert [card["id"] for card in results][0] == "regular"
    assert scryfall.getCardReprintId("regular", "fra", "en")[0] == "regular"
    printings = scryfall.getCardPrintings("regular")
    assert printings[0]["id"] == "regular"
    assert {printing["id"] for printing in printings} == {"regular", "showcase-foil", "promo"}


def test_bulk_partial_search_dedupes_by_oracle(bulkFolder):
    results = scryfall.searchCards({"name": "bolt"})
    assert [card["id"] for card in results] == ["bolt-new"]


def test_bulk_id_and_mtgo_lookups(bulkFolder):
    assert scryfall.getCardById("bolt-new")["name"] == "Lightning Bolt"
    assert scryfall.getCardById("does-not-exist") is None
    assert scryfall.getCardByMTGOId(200)["id"] == "bolt-new"
    assert scryfall.getCardByMTGOId(999999) is None


def test_cardviewer_changes_edition_twice(bulkFolder, qtApp, monkeypatch):
    from widgets.cardviewer import CardViewer

    monkeypatch.setattr(constants, "IMG_DOWNLOAD_METHOD", "direct")
    monkeypatch.setattr(scryfall, "getSetSvg", lambda setId: None)

    parent = QtWidgets.QWidget()
    parent.proxyglyphFontId = 0
    viewer = CardViewer(parent)
    viewer.setManaFont = lambda: None

    def waitFor(predicate, timeout=5):
        end = time.time() + timeout
        while time.time() < end:
            qtApp.processEvents()
            if predicate():
                return True
            time.sleep(0.01)
        return False

    viewer.display("bolt-new")
    assert waitFor(lambda: hasattr(viewer, "card") and viewer.printingSelect.count() > 1)

    def switchEdition():
        currentCardId = viewer.card["id"]
        nextIndex = next(
            i for i in range(viewer.printingSelect.count())
            if viewer.printingSelect.itemData(i) != currentCardId
        )
        viewer.printingSelect.setCurrentIndex(nextIndex)
        assert waitFor(lambda: viewer.card["id"] != currentCardId)

    switchEdition()
    switchEdition()
    viewer.deleteLater()


def test_bulk_reprints_and_reprint_ids(bulkFolder):
    assert scryfall.getCardReprints("bolt-new") == ["lea", "msc"]
    assert scryfall.getCardReprintId("bolt-new", "lea", "en") == ["bolt-old"]
    assert scryfall.getCardReprintId("bolt-new", "lea", "fr") == ["bolt-fr"]


def test_bulk_non_english_falls_back_online(bulkFolder, monkeypatch):
    calls = []

    def fakeOnline(card, setCode, lang):
        calls.append((card["id"], setCode, lang))
        return ["online-translation"]

    monkeypatch.setattr(scryfall, "_getCardReprintIdOnline", fakeOnline)
    assert scryfall.getCardReprintId("shock-new", "msc", "fr") == ["online-translation"]
    assert calls == [("shock-new", "msc", "fr")]


def test_set_icon_uses_parent_set_icon_uri(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_SET_ICONS_LOCATION", tmp_path)
    monkeypatch.setattr(scryfall, "getSetSymbol", lambda setId: None)
    monkeypatch.setattr(
        scryfall,
        "getSetData",
        lambda setId, key: "afra" if key == "code" else None,
    )
    calls = []

    def fakeJson(url, **kwargs):
        calls.append(url)
        return {"icon_svg_uri": "https://svgs.scryfall.io/sets/fra.svg?1"}

    def fakeData(url, **kwargs):
        calls.append(url)
        return "<svg/>"

    monkeypatch.setattr(scryfall.utils, "getUrlJsonData", fakeJson)
    monkeypatch.setattr(scryfall.utils, "getUrlData", fakeData)
    scryfall.resetSetIconCache()

    iconPath = scryfall.getSetSvg("set-afra")

    assert iconPath is not None
    assert (tmp_path / "set-afra.svg").read_text() == "<svg/>"
    assert calls == [
        "https://api.scryfall.com/sets/afra",
        "https://svgs.scryfall.io/sets/fra.svg?1",
    ]


def test_set_icon_failure_returns_none_and_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_SET_ICONS_LOCATION", tmp_path)
    monkeypatch.setattr(scryfall, "getSetSymbol", lambda setId: None)
    monkeypatch.setattr(
        scryfall,
        "getSetData",
        lambda setId, key: "afra" if key == "code" else None,
    )
    monkeypatch.setattr(
        scryfall.utils,
        "getUrlJsonData",
        lambda url, **kwargs: {"icon_svg_uri": "https://svgs.scryfall.io/sets/fra.svg"},
    )
    dataCalls = []

    def fakeData(url, **kwargs):
        dataCalls.append(url)
        return None

    monkeypatch.setattr(scryfall.utils, "getUrlData", fakeData)
    scryfall.resetSetIconCache()

    assert scryfall.getSetSvg("set-afra") is None
    assert scryfall.getSetSvg("set-afra") is None
    assert len(dataCalls) == 1


def test_fileData_handles_none():
    from lib import qt

    assert qt.fileData(None) is None


def test_bulk_sets_and_formats(bulkFolder):
    sets = {setData["code"]: setData for setData in scryfall.getSets()}
    assert sets["lea"]["name"] == "Limited Edition Alpha"
    assert sets["msc"]["name"] == "Modern Horizons 3 Commander"
    assert "modern" in scryfall.getFormats()


def test_bulk_loads_gzipped_jsonl(bulkFolder):
    jsonlPath = bulkFolder / "default-cards-20240201000000.jsonl.gz"
    with gzip.open(jsonlPath, "wt", encoding="utf-8") as file:
        for card in SAMPLE_CARDS:
            file.write(json.dumps(card) + "\n")
    (bulkFolder / "default-cards-20240101000000.json").unlink()
    scryfall.resetBulkDataCache()
    scryfall.resetSetsCache()

    results = scryfall.searchCards({"name": "Lightning Bolt"}, exact=True)
    assert [card["id"] for card in results] == ["bolt-new", "bolt-old"]


def test_bulk_cache_creates_sqlite_file(bulkFolder):
    assert scryfall.getBulkCardCount() == 4
    assert (bulkFolder / "default-cards-cache.sqlite3").is_file()


def test_bulk_index_reloads_when_file_changes(bulkFolder):
    assert scryfall.getBulkCardCount() == 4
    (bulkFolder / "default-cards-20240101000000.json").write_text(
        json.dumps(SAMPLE_CARDS[:1]), encoding="utf-8"
    )
    assert scryfall.getBulkCardCount() == 1


def test_bulk_manager_download_and_metadata(tmp_path, monkeypatch):
    payload = json.dumps(SAMPLE_CARDS).encode("utf-8")
    remoteInfo = {
        "type": "default_cards",
        "download_uri": "https://example.com/default-cards-20250101000000.json",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "size": len(payload),
        "etag": "test-etag",
    }

    class FakeResponse:
        status_code = 200
        headers = {"Content-Length": str(len(payload))}

        def iter_content(self, chunk_size):
            yield payload

    monkeypatch.setattr(bulk.utils, "getUrlJsonData", lambda url, **kwargs: {"data": [remoteInfo]})
    monkeypatch.setattr(bulk.requests, "get", lambda *args, **kwargs: FakeResponse())
    bulk.resetBulkInfoCache()

    manager = bulk.BulkDataManager(folder=tmp_path, bulkType="default_cards")
    downloaded = manager.downloadBulkData()

    assert downloaded.name == "default-cards-20250101000000.json"
    assert downloaded.read_bytes() == payload
    assert not list(tmp_path.glob("*.tmp"))
    assert manager.getLocalBulkFile() == downloaded
    assert manager.needsUpdate() is False

    status = manager.getStatus()
    assert status["size"] == len(payload)
    assert status["updated_at"] == remoteInfo["updated_at"]


def test_bulk_manager_download_jsonl_gz(tmp_path, monkeypatch):
    payload = gzip.compress(
        ("\n".join(json.dumps(card) for card in SAMPLE_CARDS) + "\n").encode("utf-8")
    )
    remoteInfo = {
        "type": "default_cards",
        "jsonl_download_uri": "https://example.com/default-cards-20260101000000.jsonl.gz",
        "updated_at": "2026-01-01T00:00:00.000Z",
        "compressed_size": len(payload),
    }

    class FakeResponse:
        status_code = 200
        headers = {"Content-Length": str(len(payload))}

        def iter_content(self, chunk_size):
            yield payload

    monkeypatch.setattr(bulk.utils, "getUrlJsonData", lambda url, **kwargs: {"data": [remoteInfo]})
    monkeypatch.setattr(bulk.requests, "get", lambda *args, **kwargs: FakeResponse())
    bulk.resetBulkInfoCache()

    manager = bulk.BulkDataManager(folder=tmp_path, bulkType="default_cards")
    downloaded = manager.downloadBulkData()

    assert downloaded.name.endswith(".jsonl.gz")
    assert len(list(bulk.iterBulkRecords(downloaded))) == len(SAMPLE_CARDS)
    assert manager.needsUpdate() is False


def test_bulk_manager_needs_update(tmp_path, monkeypatch):
    localFile = tmp_path / "default-cards-20240101000000.json"
    localFile.write_text(json.dumps(SAMPLE_CARDS), encoding="utf-8")
    metadata = {
        "default_cards": {
            "type": "default_cards",
            "local_path": localFile.name,
            "updated_at": "2024-01-01T00:00:00.000Z",
        }
    }
    (tmp_path / constants.BULK_METADATA_FILENAME).write_text(json.dumps(metadata), encoding="utf-8")
    remoteInfo = {
        "type": "default_cards",
        "download_uri": "https://example.com/default-cards-20250101000000.json",
        "updated_at": "2025-01-01T00:00:00.000Z",
    }
    monkeypatch.setattr(bulk.utils, "getUrlJsonData", lambda url, **kwargs: {"data": [remoteInfo]})
    bulk.resetBulkInfoCache()

    manager = bulk.BulkDataManager(folder=tmp_path, bulkType="default_cards")
    assert manager.needsUpdate() is True


def test_bulk_manager_cancel_and_corrupt_download(tmp_path, monkeypatch):
    remoteInfo = {
        "type": "default_cards",
        "download_uri": "https://example.com/default-cards-20250101000000.json",
        "updated_at": "2025-01-01T00:00:00.000Z",
    }

    class FakeResponse:
        status_code = 200
        headers = {}

        def __init__(self, payload):
            self.payload = payload

        def iter_content(self, chunk_size):
            yield self.payload

    monkeypatch.setattr(bulk.utils, "getUrlJsonData", lambda url, **kwargs: {"data": [remoteInfo]})
    bulk.resetBulkInfoCache()
    manager = bulk.BulkDataManager(folder=tmp_path, bulkType="default_cards")

    monkeypatch.setattr(bulk.requests, "get", lambda *args, **kwargs: FakeResponse(b"{}"))
    with pytest.raises(bulk.DownloadCancelled):
        manager.downloadBulkData(progress_callback=lambda downloaded, total: False)
    assert not (tmp_path / "default-cards-20250101000000.json").exists()
    assert not list(tmp_path.glob("*.tmp"))

    monkeypatch.setattr(bulk.requests, "get", lambda *args, **kwargs: FakeResponse(b"not json"))
    with pytest.raises(json.JSONDecodeError):
        manager.downloadBulkData()
    assert not (tmp_path / "default-cards-20250101000000.json").exists()
    assert not list(tmp_path.glob("*.tmp"))
