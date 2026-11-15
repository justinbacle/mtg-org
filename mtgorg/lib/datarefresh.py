"""Single entry point for refreshing online Scryfall data."""

import datetime
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import connector
import constants
from lib import cachestate, scryfall, utils


@dataclass(frozen=True)
class RefreshResult:
    updated: bool
    new_sets: tuple[str, ...] = ()


def setsFingerprint(sets: list[dict], today: str | None = None) -> str:
    """Stable fingerprint of released set metadata."""
    today = today or datetime.date.today().isoformat()
    released = sorted(
        (s.get("code", ""), s.get("name", ""), s.get("released_at", ""))
        for s in sets
        if s.get("code") and (s.get("released_at") or "") <= today
    )
    return hashlib.sha256(json.dumps(released).encode("utf-8")).hexdigest()


def newSetCodes(remoteSets: list[dict], cachedSets: list[dict], today: str | None = None) -> list[str]:
    today = today or datetime.date.today().isoformat()
    cachedCodes = {s.get("code") for s in cachedSets}
    return sorted(
        s["code"] for s in remoteSets
        if s.get("code")
        and s["code"] not in cachedCodes
        and (s.get("released_at") or "") <= today
    )


def checkForUpdates() -> RefreshResult:
    """Refresh sets and invalidate cached cards when set metadata changes."""
    if constants.USE_BULK_FILES:
        return RefreshResult(False)

    setsPath = Path(constants.DEFAULT_INFOS_LOCATION) / "sets.json"
    remoteData = scryfall.getOnlineSetData()
    remoteSets = remoteData.get("sets") or []
    fingerprint = setsFingerprint(remoteSets)
    state = cachestate.load()
    if state.get("sets_fingerprint") == fingerprint and setsPath.is_file():
        return RefreshResult(False)

    oldSets = (utils.loadJson(setsPath) or {}).get("sets") or []
    newCodes = newSetCodes(remoteSets, oldSets)
    utils.saveJson(remoteData, setsPath)
    cachestate.bumpCardGeneration(fingerprint)
    connector.pruneOldCards()
    scryfall.resetDataCaches()
    try:
        utils.updateKeyRuneIfMissing(newCodes)
    except Exception as e:
        logging.warning(f"Could not refresh Keyrune for new sets: {e}")
    logging.info(f"Scryfall set data updated; new sets: {', '.join(newCodes) or 'none'}")
    return RefreshResult(True, tuple(newCodes))
