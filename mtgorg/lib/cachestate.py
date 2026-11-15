"""Small manifest tracking which card-cache generation is current."""

import json
import logging
import os
import threading
from pathlib import Path

import constants
from lib import utils

_lock = threading.RLock()
DEFAULT_STATE = {"sets_fingerprint": "", "card_generation": 1}


def statePath() -> Path:
    return Path(constants.DEFAULT_INFOS_LOCATION) / "data_version.json"


def load() -> dict:
    with _lock:
        try:
            data = utils.loadJson(statePath())
        except (OSError, ValueError) as e:
            logging.warning(f"Could not read cache state: {e}")
            data = None
        if not isinstance(data, dict):
            return dict(DEFAULT_STATE)
        state = dict(DEFAULT_STATE)
        state.update(data)
        return state


def save(state: dict) -> None:
    with _lock:
        path = statePath()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmpPath = path.with_suffix(path.suffix + ".tmp")
        with open(tmpPath, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=4)
        os.replace(tmpPath, path)


def getCardGeneration() -> int:
    try:
        return int(load()["card_generation"])
    except (TypeError, ValueError):
        logging.warning("Invalid card cache generation, resetting to 1")
        return 1


def bumpCardGeneration(sets_fingerprint: str) -> int:
    with _lock:
        state = load()
        state["sets_fingerprint"] = sets_fingerprint
        state["card_generation"] = getCardGeneration() + 1
        save(state)
        return state["card_generation"]
