"""Cached Scryfall/Tagger oracle tags."""

import gzip
import json
import logging
import os
import threading
from pathlib import Path

import requests

import constants
from lib import utils

BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
BULK_TYPE = "oracle_tags"
_indexLock = threading.RLock()
_memoryIndex: dict[str, list[str]] | None = None
_failed = False


def indexPath() -> Path:
    return Path(constants.DEFAULT_INFOS_LOCATION) / "oracle_tags.json"


def _localBulkPath() -> Path:
    return Path(constants.DEFAULT_BULK_FOLDER_LOCATION) / "oracle-tags.jsonl.gz"


def _download(url: str) -> Path:
    path = _localBulkPath()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with requests.get(url, headers=utils.DEFAULT_HEADERS, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(tmp, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
    os.replace(tmp, path)
    return path


def _buildIndex(updatedAt: str = "") -> dict[str, list[str]]:
    bulkPath = _localBulkPath()
    if not bulkPath.is_file():
        remote = utils.getUrlJsonData(BULK_DATA_URL)
        if remote is None:
            return {}
        info = next((item for item in remote.get("data", []) if item.get("type") == BULK_TYPE), None)
        if info is None or not info.get("jsonl_download_uri"):
            logging.warning("Scryfall oracle-tags bulk data unavailable")
            return {}
        _download(info["jsonl_download_uri"])
        updatedAt = str(info.get("updated_at", ""))
    index: dict[str, set[str]] = {}
    with gzip.open(bulkPath, "rt", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            tag = json.loads(line)
            label = tag.get("label")
            if not label:
                continue
            for tagging in tag.get("taggings", []):
                oracleId = tagging.get("oracle_id")
                if oracleId:
                    index.setdefault(oracleId, set()).add(label)
    mapping = {oracleId: sorted(labels) for oracleId, labels in index.items()}
    utils.saveJson({"_updated_at": updatedAt, "tags": mapping}, indexPath())
    return mapping


def _load() -> dict[str, list[str]]:
    global _memoryIndex, _failed
    with _indexLock:
        if _memoryIndex is not None:
            return _memoryIndex
        if _failed:
            return {}
        try:
            data = utils.loadJson(indexPath()) or {}
            mapping = data.get("tags")
            if not isinstance(mapping, dict):
                mapping = _buildIndex()
        except Exception as e:
            logging.warning(f"Could not load oracle tags: {e}")
            _failed = True
            return {}
        _memoryIndex = mapping
        return mapping


def getTags(oracleId: str | None) -> list[str]:
    if not oracleId:
        return []
    return _load().get(oracleId, [])


def hasCache() -> bool:
    return indexPath().is_file()


def getCachedTags(oracleId: str | None) -> list[str]:
    """Return tags only from an existing cache; never downloads or builds."""
    global _memoryIndex
    if not oracleId:
        return []
    with _indexLock:
        if _memoryIndex is not None:
            return _memoryIndex.get(oracleId, [])
        try:
            data = utils.loadJson(indexPath()) or {}
        except (OSError, ValueError):
            return []
        mapping = data.get("tags") if isinstance(data, dict) else None
        if not isinstance(mapping, dict):
            return []
        _memoryIndex = mapping
        return mapping.get(oracleId, [])
