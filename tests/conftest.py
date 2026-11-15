import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from tests import fake_scryfall

# The app derives all of its cache/DB paths from the user's home directory at
# import time. Point tests at a throwaway home so they never touch the real
# ~/.mtgo cache and each run starts from a known state.
_TEST_HOME = Path(tempfile.mkdtemp(prefix="mtgorg-tests-"))
os.environ["HOME"] = str(_TEST_HOME)
os.environ["USERPROFILE"] = str(_TEST_HOME)
(_TEST_HOME / ".mtgo").mkdir(parents=True, exist_ok=True)
atexit.register(shutil.rmtree, _TEST_HOME, ignore_errors=True)


@pytest.fixture(autouse=True)
def _fakeScryfall(monkeypatch):
    """Replace live Scryfall calls unless MTGORG_TEST_ONLINE=1 is set."""
    if os.environ.get("MTGORG_TEST_ONLINE") == "1":
        yield
        return

    from lib import scryfall

    for name in ("searchCards", "getSets", "getCardById", "getCardReprints", "getCardByMTGOId"):
        monkeypatch.setattr(scryfall, name, getattr(fake_scryfall, name))
    yield
