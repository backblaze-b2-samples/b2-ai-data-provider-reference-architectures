import pytest

from cvat_b2_pipeline import config
from cvat_b2_pipeline.config import ConfigError


def _clear(monkeypatch):
    for n in (*config.REQUIRED, "B2_ENDPOINT"):
        monkeypatch.delenv(n, raising=False)


def test_missing_env_lists_names_only(monkeypatch, tmp_path):
    _clear(monkeypatch)
    monkeypatch.setenv("B2_APPLICATION_KEY", "topsecret")
    with pytest.raises(ConfigError) as e:
        config.load(str(tmp_path / "none.env"))
    assert "B2_BUCKET_NAME" in str(e.value) and "topsecret" not in str(e.value)


def test_endpoint_derived_from_region_and_secret_not_in_repr(monkeypatch, tmp_path):
    _clear(monkeypatch)
    for n, v in zip(config.REQUIRED, ("id", "topsecret", "bkt", "eu-central-003")):
        monkeypatch.setenv(n, v)
    cfg = config.load(str(tmp_path / "none.env"))
    assert cfg.endpoint == "https://s3.eu-central-003.backblazeb2.com"
    assert "topsecret" not in repr(cfg)


def test_endpoint_override(monkeypatch, tmp_path):
    _clear(monkeypatch)
    for n, v in zip(config.REQUIRED, ("id", "k", "bkt", "r")):
        monkeypatch.setenv(n, v)
    monkeypatch.setenv("B2_ENDPOINT", "https://example.test")
    assert config.load(str(tmp_path / "none.env")).endpoint == "https://example.test"
