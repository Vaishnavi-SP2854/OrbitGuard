import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ingestion import celestrak_ingest as ing  # noqa: E402

SAMPLE = [{"OBJECT_NAME": "ISS (ZARYA)", "NORAD_CAT_ID": 25544}]


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def raw_file(tmp_path, monkeypatch):
    f = tmp_path / "active.json"
    monkeypatch.setattr(ing, "RAW_FILE", f)
    return f


def _fail_if_called(*args, **kwargs):
    raise AssertionError("network should not be used")


def test_settings_define_ingestion_constants():
    from config import settings

    assert settings.RAW_FILE.name.endswith(".json")
    assert settings.CACHE_MAX_AGE_HOURS > 0


def test_downloads_and_caches_when_no_file(raw_file, monkeypatch):
    monkeypatch.setattr(ing.requests, "get", lambda *a, **k: FakeResponse(SAMPLE))
    assert ing.run_ingestion() == str(raw_file)
    assert json.loads(raw_file.read_text()) == SAMPLE


def test_uses_fresh_cache_without_network(raw_file, monkeypatch):
    raw_file.write_text(json.dumps(SAMPLE))
    monkeypatch.setattr(ing.requests, "get", _fail_if_called)
    assert ing.run_ingestion() == str(raw_file)


def test_force_redownloads_even_if_cache_is_fresh(raw_file, monkeypatch):
    raw_file.write_text(json.dumps([]))
    monkeypatch.setattr(ing.requests, "get", lambda *a, **k: FakeResponse(SAMPLE))
    ing.run_ingestion(force=True)
    assert json.loads(raw_file.read_text()) == SAMPLE


def test_stale_cache_triggers_download(raw_file, monkeypatch):
    raw_file.write_text(json.dumps([]))
    old = time.time() - (ing.CACHE_MAX_AGE_HOURS + 1) * 3600
    os.utime(raw_file, (old, old))
    monkeypatch.setattr(ing.requests, "get", lambda *a, **k: FakeResponse(SAMPLE))
    ing.run_ingestion()
    assert json.loads(raw_file.read_text()) == SAMPLE


def test_falls_back_to_stale_cache_when_network_fails(raw_file, monkeypatch):
    raw_file.write_text(json.dumps(SAMPLE))
    old = time.time() - (ing.CACHE_MAX_AGE_HOURS + 1) * 3600
    os.utime(raw_file, (old, old))

    def boom(*a, **k):
        raise ing.requests.ConnectionError("offline")

    monkeypatch.setattr(ing.requests, "get", boom)
    assert ing.run_ingestion() == str(raw_file)


def test_returns_none_when_offline_and_no_cache(raw_file, monkeypatch):
    def boom(*a, **k):
        raise ing.requests.ConnectionError("offline")

    monkeypatch.setattr(ing.requests, "get", boom)
    assert ing.run_ingestion() is None


def test_non_list_response_is_rejected(raw_file, monkeypatch):
    monkeypatch.setattr(ing.requests, "get", lambda *a, **k: FakeResponse({"error": "throttled"}))
    assert ing.run_ingestion() is None
    assert not raw_file.exists()