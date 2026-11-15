"""GitHub release update checks."""

import datetime
import logging
import re

import requests

import config
import constants

RELEASES_URL = "https://api.github.com/repos/justinbacle/mtg-org/releases/latest"
CHECK_INTERVAL = datetime.timedelta(hours=24)


def _versionTuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def isNewer(remote: str, current: str) -> bool:
    remoteParts = _versionTuple(remote)
    currentParts = _versionTuple(current)
    if not remoteParts or not currentParts:
        return False
    return remoteParts > currentParts


def _checkDue(settings: dict) -> bool:
    if not settings["auto_check"]:
        return False
    lastCheck = settings.get("last_check", "")
    if not lastCheck:
        return True
    try:
        last = datetime.datetime.strptime(lastCheck, constants.DATETIME_FORMAT)
    except ValueError:
        return True
    return datetime.datetime.now() - last >= CHECK_INTERVAL


def checkForUpdate(force: bool = False) -> dict | None:
    settings = config.getUpdateSettings()
    if not force and not _checkDue(settings):
        return None
    try:
        response = requests.get(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github+json"},
            timeout=15,
        )
    except requests.RequestException as e:
        logging.warning(f"Could not check for updates: {e}")
        return None
    if response.status_code != 200:
        logging.warning(f"Update check failed with HTTP {response.status_code}")
        return None
    data = response.json()
    config.saveUpdateCheck(datetime.datetime.now().strftime(constants.DATETIME_FORMAT))
    tag = str(data.get("tag_name", ""))
    if not tag or tag == settings.get("skipped_version"):
        return None
    if not isNewer(tag, constants.appVersion()):
        return None
    return {
        "version": tag,
        "url": data.get("html_url"),
        "body": data.get("body") or "",
    }
