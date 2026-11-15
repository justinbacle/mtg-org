import datetime
import gzip
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

import constants
from lib import utils


BULK_DATA_URL = "https://api.scryfall.com/bulk-data"

_bulkInfoCache: dict = {
    "folder": None,
    "fetched_at": None,
    "data": None,
}


class DownloadCancelled(Exception):
    """Raised when the user cancels a bulk-data download."""


def resetBulkInfoCache():
    global _bulkInfoCache
    _bulkInfoCache = {"folder": None, "fetched_at": None, "data": None}


def _isBulkFileName(name: str) -> bool:
    return name.endswith((".json", ".jsonl", ".jsonl.gz"))


def iterBulkRecords(path: str | Path, fileName: str | None = None):
    """Yield card records from a Scryfall bulk file (JSON, JSONL, or gzipped JSONL)."""
    path = Path(path)
    name = (fileName if fileName is not None else path.name).lower()
    if name.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    yield json.loads(line)
    elif name.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    yield json.loads(line)
    else:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError(f"{path} does not contain a JSON list")
        yield from data


def _downloadUri(remoteInfo: dict) -> str | None:
    return remoteInfo.get("download_uri") or remoteInfo.get("jsonl_download_uri")


def _remoteSize(remoteInfo: dict) -> int:
    return int(remoteInfo.get("size") or remoteInfo.get("compressed_size") or 0)


def _validateBulkFile(path: Path, fileName: str):
    recordCount = 0
    for record in iterBulkRecords(path, fileName):
        if not isinstance(record, dict):
            raise ValueError(f"Bulk file {path} contains a non-object record")
        recordCount += 1
    if recordCount == 0:
        raise ValueError(f"Bulk file {path} is empty")


class BulkDataManager:
    """Download and track Scryfall bulk-data files."""

    def __init__(self, folder: str | Path | None = None, bulkType: str | None = None):
        self.folder = Path(folder if folder is not None else constants.DEFAULT_BULK_FOLDER_LOCATION)
        self.bulkType = bulkType if bulkType is not None else self.getActiveBulkType()

    @staticmethod
    def getBulkTypeForMode(languageMode: str | None = None) -> str:
        mode = languageMode if languageMode is not None else constants.BULK_LANGUAGE_MODE
        return constants.BULK_DATA_TYPES.get(mode, "default_cards")

    @staticmethod
    def getActiveBulkType() -> str:
        return BulkDataManager.getBulkTypeForMode(constants.BULK_LANGUAGE_MODE)

    @property
    def metadataPath(self) -> Path:
        return self.folder / constants.BULK_METADATA_FILENAME

    def _filePrefix(self, bulkType: str | None = None) -> str:
        return (bulkType if bulkType is not None else self.bulkType).replace("_", "-")

    def _loadMetadata(self) -> dict:
        if not self.metadataPath.is_file():
            return {}
        try:
            with open(self.metadataPath, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as e:
            logging.warning(f"Could not read bulk metadata: {e}")
            return {}
        return data if isinstance(data, dict) else {}

    def _saveMetadata(self, metadata: dict):
        self.folder.mkdir(parents=True, exist_ok=True)
        tmpPath = self.metadataPath.with_suffix(self.metadataPath.suffix + ".tmp")
        with open(tmpPath, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)
        os.replace(tmpPath, self.metadataPath)

    def fetchBulkInfo(self, force: bool = False) -> list[dict]:
        global _bulkInfoCache
        now = datetime.datetime.now()
        cacheFresh = (
            _bulkInfoCache["data"] is not None
            and _bulkInfoCache["folder"] == str(self.folder)
            and _bulkInfoCache["fetched_at"] is not None
            and (now - _bulkInfoCache["fetched_at"]).total_seconds() < constants.BULK_INFO_CACHE_SECONDS
        )
        if force or not cacheFresh:
            data = utils.getUrlJsonData(BULK_DATA_URL)
            if data is None or "data" not in data:
                raise RuntimeError("Could not fetch Scryfall bulk-data metadata")
            _bulkInfoCache = {
                "folder": str(self.folder),
                "fetched_at": now,
                "data": data["data"],
            }
        return _bulkInfoCache["data"]

    def getRemoteInfo(self, bulkType: str | None = None) -> dict:
        bulkType = bulkType if bulkType is not None else self.bulkType
        for bulkInfo in self.fetchBulkInfo():
            if bulkInfo.get("type") == bulkType:
                return bulkInfo
        raise RuntimeError(f"Scryfall does not offer bulk data type {bulkType!r}")

    def getLocalBulkFile(self, bulkType: str | None = None) -> Path | None:
        bulkType = bulkType if bulkType is not None else self.bulkType
        metadata = self._loadMetadata().get(bulkType, {})
        localPath = metadata.get("local_path")
        if localPath:
            candidate = self.folder / Path(localPath).name
            if _isBulkFileName(candidate.name) and candidate.is_file() and candidate.stat().st_size > 0:
                return candidate

        prefix = self._filePrefix(bulkType)
        candidates = [
            path for path in self.folder.glob(f"{prefix}-*")
            if path.is_file() and _isBulkFileName(path.name) and path.stat().st_size > 0
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

    def needsUpdate(self, bulkType: str | None = None) -> bool:
        bulkType = bulkType if bulkType is not None else self.bulkType
        localFile = self.getLocalBulkFile(bulkType)
        if localFile is None:
            return True
        remoteInfo = self.getRemoteInfo(bulkType)
        metadata = self._loadMetadata().get(bulkType, {})
        if metadata.get("local_path") != localFile.name or not metadata.get("updated_at"):
            return True
        return str(remoteInfo.get("updated_at", "")) > str(metadata.get("updated_at", ""))

    def downloadBulkData(self, bulkType: str | None = None, progress_callback=None) -> Path:
        bulkType = bulkType if bulkType is not None else self.bulkType
        remoteInfo = self.getRemoteInfo(bulkType)
        downloadUri = _downloadUri(remoteInfo)
        if not downloadUri:
            raise RuntimeError(f"Bulk data type {bulkType!r} has no download URI")

        self.folder.mkdir(parents=True, exist_ok=True)
        finalName = Path(urlparse(downloadUri).path).name
        if not finalName:
            raise RuntimeError(f"Could not determine a filename for {downloadUri!r}")
        finalPath = self.folder / finalName
        tmpPath = finalPath.with_suffix(finalPath.suffix + ".tmp")
        if tmpPath.exists():
            tmpPath.unlink()

        response = requests.get(downloadUri, stream=True, headers=utils.DEFAULT_HEADERS)
        if response.status_code != 200:
            raise RuntimeError(f"Bulk download failed with HTTP {response.status_code}")

        totalBytes = int(response.headers.get("Content-Length", 0) or _remoteSize(remoteInfo))
        downloadedBytes = 0
        try:
            with open(tmpPath, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    file.write(chunk)
                    downloadedBytes += len(chunk)
                    if progress_callback is not None and progress_callback(downloadedBytes, totalBytes) is False:
                        raise DownloadCancelled
            _validateBulkFile(tmpPath, finalName)
        except Exception:
            tmpPath.unlink(missing_ok=True)
            raise

        os.replace(tmpPath, finalPath)

        metadata = self._loadMetadata()
        metadata[bulkType] = {
            "type": bulkType,
            "download_uri": downloadUri,
            "updated_at": remoteInfo.get("updated_at", ""),
            "size": downloadedBytes,
            "etag": remoteInfo.get("etag"),
            "local_path": finalPath.name,
            "downloaded_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        self._saveMetadata(metadata)
        self.cleanupOldBulkFiles()
        return finalPath

    def cleanupOldBulkFiles(self, keep: int = 2):
        for bulkType in set(constants.BULK_DATA_TYPES.values()):
            prefix = self._filePrefix(bulkType)
            files = sorted(
                (
                    path for path in self.folder.glob(f"{prefix}-*")
                    if path.is_file() and _isBulkFileName(path.name)
                ),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            for oldFile in files[keep:]:
                logging.info(f"Removing old bulk file {oldFile}")
                oldFile.unlink(missing_ok=True)

    def getStatus(self, bulkType: str | None = None) -> dict:
        bulkType = bulkType if bulkType is not None else self.bulkType
        localFile = self.getLocalBulkFile(bulkType)
        metadata = self._loadMetadata().get(bulkType, {})
        return {
            "bulk_type": bulkType,
            "local_path": localFile,
            "size": localFile.stat().st_size if localFile is not None else 0,
            "updated_at": metadata.get("updated_at", ""),
            "downloaded_at": metadata.get("downloaded_at", ""),
        }
