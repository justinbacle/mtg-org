import os

import pytest

from lib import bulk


pytestmark = pytest.mark.live


def requireLiveBulk():
    if os.environ.get("MTGORG_TEST_LIVE_BULK") != "1":
        pytest.skip("set MTGORG_TEST_LIVE_BULK=1 to run live Scryfall bulk tests")


def test_live_bulk_metadata(tmp_path):
    requireLiveBulk()
    manager = bulk.BulkDataManager(folder=tmp_path, bulkType="default_cards")

    info = manager.getRemoteInfo()

    assert bulk._downloadUri(info) is not None
    assert bulk._remoteSize(info) > 0
    assert info.get("updated_at")


def test_live_bulk_download_and_read(tmp_path):
    requireLiveBulk()
    manager = bulk.BulkDataManager(folder=tmp_path, bulkType="default_cards")

    downloaded = manager.downloadBulkData()

    assert downloaded.is_file()
    assert downloaded.stat().st_size > 0
    records = bulk.iterBulkRecords(downloaded)
    firstRecord = next(records)
    assert "id" in firstRecord
    assert "name" in firstRecord
    assert manager.getLocalBulkFile() == downloaded
    assert manager.getStatus()["updated_at"]
