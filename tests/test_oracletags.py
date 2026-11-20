import constants
from lib import oracletags, utils


def test_get_tags_reads_cached_index(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DEFAULT_INFOS_LOCATION", tmp_path)
    utils.saveJson({"tags": {"oracle-1": ["ramp", "tutor"]}}, tmp_path / "oracle_tags.json")
    monkeypatch.setattr(oracletags, "_memoryIndex", None)
    monkeypatch.setattr(oracletags, "_failed", False)

    assert oracletags.getTags("oracle-1") == ["ramp", "tutor"]
    assert oracletags.getTags("missing") == []
    assert oracletags.getTags(None) == []
