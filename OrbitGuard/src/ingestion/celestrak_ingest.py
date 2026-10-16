"""Download GP (OMM/JSON) data from CelesTrak, with local caching."""
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import CELESTRAK_ACTIVE_URL, CACHE_MAX_AGE_HOURS, RAW_FILE  # noqa: E402

HEADERS = {"User-Agent": "OrbitGuard-student-project/1.0"}


def run_ingestion(force: bool = False):
    """Return path of the raw JSON file, or None if unavailable."""
    if RAW_FILE.exists() and not force:
        age_h = (time.time() - RAW_FILE.stat().st_mtime) / 3600
        if age_h < CACHE_MAX_AGE_HOURS:
            print(f"Using cached data ({age_h:.1f} h old): {RAW_FILE}")
            return str(RAW_FILE)

    print(f"Connecting to CelesTrak...\nURL: {CELESTRAK_ACTIVE_URL}")
    try:
        resp = requests.get(CELESTRAK_ACTIVE_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):  # CelesTrak returns text errors/throttle msgs
            raise ValueError(f"Unexpected response: {str(data)[:200]}")
        RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"SUCCESS: {len(data)} objects saved to {RAW_FILE}")
        return str(RAW_FILE)
    except Exception as e:  # noqa: BLE001
        print(f"Fetch error: {e}")
        if RAW_FILE.exists():
            print(f"Falling back to older cached file: {RAW_FILE}")
            return str(RAW_FILE)
        print("No cached data. Check your internet connection / try again in 2 hours.")
        return None


if __name__ == "__main__":
    run_ingestion(force="--force" in sys.argv)
