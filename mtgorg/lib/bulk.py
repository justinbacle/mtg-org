import datetime
import gzip
import json
import logging
import os
import re
import sqlite3
import threading
from contextlib import contextmanager
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


def _numericValue(value) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _oracleText(record: dict) -> str:
    if "oracle_text" in record:
        return record.get("oracle_text", "")
    return " ".join(face.get("oracle_text", "") for face in record.get("card_faces", []))


class BulkCache:
    """Disk-backed card cache built from a bulk file."""

    SCHEMA_VERSION = 3
    BATCH_SIZE = 1000

    def __init__(self, folder: str | Path, bulkType: str, sourcePath: str | Path):
        self.folder = Path(folder)
        self.bulkType = bulkType
        self.sourcePath = Path(sourcePath)
        self.dbPath = self.folder / f"{bulkType.replace('_', '-')}-cache.sqlite3"
        self._lock = threading.RLock()
        self._ready = False
        self._readySource = None
        self._distinctNames = None

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.dbPath, timeout=30)
        try:
            yield connection
        finally:
            connection.close()

    def _sourceStat(self) -> tuple[float, int]:
        stat = self.sourcePath.stat()
        return stat.st_mtime, stat.st_size

    def _isCurrent(self) -> bool:
        if not self.dbPath.is_file():
            return False
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT source_path, source_mtime, source_size, schema_version FROM meta LIMIT 1"
                ).fetchone()
        except sqlite3.Error:
            return False
        if row is None:
            return False
        sourcePath, sourceMtime, sourceSize, schemaVersion = row
        currentMtime, currentSize = self._sourceStat()
        return (
            sourcePath == str(self.sourcePath)
            and float(sourceMtime) == currentMtime
            and int(sourceSize) == currentSize
            and int(schemaVersion) == self.SCHEMA_VERSION
        )

    def _build(self, progress_callback=None):
        logging.info(f"Building bulk cache for {self.sourcePath.name}...")
        tmpPath = self.dbPath.with_suffix(self.dbPath.suffix + ".tmp")
        tmpPath.unlink(missing_ok=True)
        connection = sqlite3.connect(tmpPath)
        try:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")
            connection.execute(
                """
                CREATE TABLE cards (
                    id TEXT PRIMARY KEY,
                    oracle_id TEXT,
                    name TEXT,
                    name_lower TEXT,
                    mtgo_id INTEGER,
                    set_code TEXT,
                    set_id TEXT,
                    set_name TEXT,
                    lang TEXT,
                    collector_number TEXT,
                    released_at TEXT,
                    cmc REAL,
                    rarity TEXT,
                    type_line TEXT,
                    colors TEXT,
                    oracle_text TEXT,
                    power TEXT,
                    toughness TEXT,
                    loyalty TEXT,
                    power_num REAL,
                    toughness_num REAL,
                    loyalty_num REAL,
                    games TEXT,
                    legalities TEXT,
                    prices TEXT,
                    data TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE meta (
                    source_path TEXT,
                    source_mtime REAL,
                    source_size INTEGER,
                    schema_version INTEGER,
                    record_count INTEGER
                )
                """
            )
            batch = []
            recordCount = 0
            for record in iterBulkRecords(self.sourcePath):
                cardId = record.get("id")
                if cardId is None:
                    continue
                batch.append((
                    cardId,
                    record.get("oracle_id"),
                    record.get("name", ""),
                    record.get("name", "").lower(),
                    record.get("mtgo_id"),
                    record.get("set"),
                    record.get("set_id"),
                    record.get("set_name"),
                    record.get("lang", "en"),
                    record.get("collector_number"),
                    record.get("released_at", ""),
                    record.get("cmc"),
                    record.get("rarity"),
                    record.get("type_line", ""),
                    "".join(sorted(color.lower() for color in record.get("colors", []))),
                    _oracleText(record).lower(),
                    record.get("power"),
                    record.get("toughness"),
                    record.get("loyalty"),
                    _numericValue(record.get("power")),
                    _numericValue(record.get("toughness")),
                    _numericValue(record.get("loyalty")),
                    ",".join(record.get("games", [])),
                    json.dumps(record.get("legalities", {}), separators=(",", ":")),
                    json.dumps(record.get("prices", {}), separators=(",", ":")),
                    json.dumps(record, ensure_ascii=False, separators=(",", ":")),
                ))
                recordCount += 1
                if len(batch) >= self.BATCH_SIZE:
                    connection.executemany(
                        "INSERT OR REPLACE INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        batch,
                    )
                    batch.clear()
                    if progress_callback is not None:
                        progress_callback(recordCount)
            if batch:
                connection.executemany(
                    "INSERT OR REPLACE INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    batch,
                )
            connection.execute("CREATE INDEX idx_cards_name ON cards(name_lower)")
            connection.execute("CREATE INDEX idx_cards_oracle ON cards(oracle_id)")
            connection.execute("CREATE INDEX idx_cards_mtgo ON cards(mtgo_id)")
            connection.execute("CREATE INDEX idx_cards_set ON cards(set_code)")
            connection.execute("CREATE INDEX idx_cards_cmc ON cards(cmc)")
            connection.execute("CREATE INDEX idx_cards_rarity ON cards(rarity)")
            connection.execute("CREATE INDEX idx_cards_power ON cards(power_num)")
            connection.execute("CREATE INDEX idx_cards_toughness ON cards(toughness_num)")
            connection.execute("CREATE INDEX idx_cards_loyalty ON cards(loyalty_num)")
            mtime, size = self._sourceStat()
            connection.execute(
                "INSERT INTO meta VALUES (?,?,?,?,?)",
                (str(self.sourcePath), mtime, size, self.SCHEMA_VERSION, recordCount),
            )
            connection.commit()
        except Exception:
            connection.close()
            tmpPath.unlink(missing_ok=True)
            raise
        connection.close()
        if recordCount == 0:
            tmpPath.unlink(missing_ok=True)
            raise RuntimeError(f"Bulk file {self.sourcePath} is empty")
        os.replace(tmpPath, self.dbPath)
        self._ready = True
        self._readySource = self._sourceStat()
        self._distinctNames = None
        logging.info(f"Bulk cache built with {recordCount} records")

    def ensureReady(self, progress_callback=None) -> bool:
        with self._lock:
            currentStat = self._sourceStat()
            if self._ready and self._readySource == currentStat and self.dbPath.is_file():
                return True
            if self._isCurrent():
                self._ready = True
                self._readySource = currentStat
                return True
            self._build(progress_callback=progress_callback)
            return True

    def _fetchAll(self, query: str, params: tuple = ()) -> list[dict]:
        with self._lock:
            self.ensureReady()
            with self._connect() as connection:
                rows = connection.execute(query, params).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _fetchOne(self, query: str, params: tuple = ()) -> dict | None:
        cards = self._fetchAll(query, params)
        return cards[0] if cards else None

    def count(self) -> int:
        with self._lock:
            self.ensureReady()
            with self._connect() as connection:
                row = connection.execute("SELECT COUNT(*) FROM cards").fetchone()
        return int(row[0]) if row is not None else 0

    def getCardById(self, cardId: str) -> dict | None:
        return self._fetchOne("SELECT data FROM cards WHERE id=? LIMIT 1", (cardId,))

    def getCardByMTGOId(self, mtgoId: int) -> dict | None:
        return self._fetchOne("SELECT data FROM cards WHERE mtgo_id=? LIMIT 1", (mtgoId,))

    def getCardsByName(self, name: str) -> list[dict]:
        return self._fetchAll("SELECT data FROM cards WHERE name_lower=?", (name.lower(),))

    def getDistinctNames(self) -> list[str]:
        with self._lock:
            self.ensureReady()
            if self._distinctNames is None:
                with self._connect() as connection:
                    self._distinctNames = [
                        row[0] for row in connection.execute("SELECT DISTINCT name_lower FROM cards")
                    ]
            return self._distinctNames

    def searchNameSubstring(self, needle: str) -> list[dict]:
        escaped = needle.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return self._fetchAll(
            "SELECT data FROM cards WHERE name_lower LIKE ? ESCAPE '\\'",
            (f"%{escaped}%",),
        )

    def getCardsByOracleId(self, oracleId: str) -> list[dict]:
        if oracleId is None:
            return []
        return self._fetchAll("SELECT data FROM cards WHERE oracle_id=?", (oracleId,))

    def _filterClauses(self, searchDict: dict) -> tuple[list[str], list]:
        clauses = []
        params = []
        setCode = searchDict.get("set") or searchDict.get("in")
        if setCode:
            clauses.append("LOWER(set_code)=?")
            params.append(str(setCode).lower())
        lang = searchDict.get("lang")
        if lang not in (None, "", "any"):
            clauses.append("lang=?")
            params.append(lang)
        rarity = searchDict.get("rarity")
        if rarity:
            clauses.append("rarity=?")
            params.append(rarity)
        cmcFilter = searchDict.get("cmc")
        if isinstance(cmcFilter, (list, tuple)) and len(cmcFilter) >= 2 and str(cmcFilter[1]).strip() != "":
            operator = cmcFilter[0] if cmcFilter[0] in ("<", ">", "=", "<=", ">=") else "="
            clauses.append(f"cmc {operator} ?")
            params.append(float(cmcFilter[1]))
        for filterKey, column in (("pow", "power_num"), ("tou", "toughness_num"), ("loy", "loyalty_num")):
            filterValue = searchDict.get(filterKey)
            if filterValue:
                match = re.fullmatch(r"\s*(<=|>=|=|<|>)\s*(-?\d+(?:\.\d+)?)\s*", str(filterValue))
                if match is not None:
                    operator, target = match.groups()
                    clauses.append(f"{column} {operator} ?")
                    params.append(float(target))
        for cardType in searchDict.get("types", []):
            if cardType:
                clauses.append("LOWER(type_line) LIKE ?")
                params.append(f"%{cardType.lower()}%")
        colorFilter = searchDict.get("colors")
        if colorFilter:
            requested = re.findall(r"(?<!-)\bc:([wubrg]+)", colorFilter)
            excluded = re.findall(r"-c:([wubrg]+)", colorFilter)
            for group in requested:
                for color in group:
                    clauses.append("colors LIKE ?")
                    params.append(f"%{color}%")
            for group in excluded:
                for color in group:
                    clauses.append("colors NOT LIKE ?")
                    params.append(f"%{color}%")
        oracle = searchDict.get("oracle", "")
        if oracle:
            clauses.append("LOWER(oracle_text) LIKE ?")
            params.append(f"%{oracle.lower()}%")
        formatName = searchDict.get("f")
        if formatName:
            clauses.append("json_extract(legalities, ?)='legal'")
            params.append(f"$.{formatName}")
        if searchDict.get("game") == "paper":
            clauses.append("games LIKE ?")
            params.append("%paper%")
        priceFilter = searchDict.get("price")
        if priceFilter:
            match = re.fullmatch(r"(eur|usd|tix)(<=|>=|=|<|>)(\d+(?:\.\d+)?)", str(priceFilter))
            if match is not None:
                currency, operator, target = match.groups()
                clauses.append(f"CAST(json_extract(prices, ?) AS REAL) {operator} ?")
                params.extend([f"$.{currency}", float(target)])
        return clauses, params

    def iterCardsFiltered(self, searchDict: dict, limit: int | None = None):
        clauses, params = self._filterClauses(searchDict)
        query = "SELECT data FROM cards"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        with self._lock:
            self.ensureReady()
            with self._connect() as connection:
                for row in connection.execute(query, params):
                    yield json.loads(row[0])

    def iterCards(self):
        with self._lock:
            self.ensureReady()
            with self._connect() as connection:
                for row in connection.execute("SELECT data FROM cards"):
                    yield json.loads(row[0])

    def getAnyCard(self) -> dict | None:
        return self._fetchOne("SELECT data FROM cards LIMIT 1")

    def getRandomCard(self) -> dict | None:
        return self._fetchOne("SELECT data FROM cards ORDER BY RANDOM() LIMIT 1")

    def getSets(self) -> list[dict]:
        with self._lock:
            self.ensureReady()
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT set_code, COALESCE(set_id, set_code), set_name, MIN(released_at)
                    FROM cards
                    GROUP BY set_code
                    ORDER BY MIN(released_at)
                    """
                ).fetchall()
        return [
            {
                "id": set_id,
                "code": set_code,
                "name": set_name or set_code,
                "released_at": released_at,
            }
            for set_code, set_id, set_name, released_at in rows
        ]


_bulkCacheRegistry: dict[tuple[str, str], BulkCache] = {}
_bulkCacheLock = threading.Lock()


def getBulkCache() -> BulkCache:
    manager = BulkDataManager()
    sourcePath = manager.getLocalBulkFile()
    if sourcePath is None:
        raise RuntimeError("No Scryfall bulk file available")
    key = (str(manager.folder), manager.bulkType)
    with _bulkCacheLock:
        current = _bulkCacheRegistry.get(key)
        if current is None or current.sourcePath != sourcePath:
            current = BulkCache(manager.folder, manager.bulkType, sourcePath)
            _bulkCacheRegistry[key] = current
    return current


def resetBulkCaches():
    with _bulkCacheLock:
        _bulkCacheRegistry.clear()
