from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "orbitguard.duckdb"
RAW_FILE = DATA_RAW_DIR / "active.json"

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CELESTRAK_ACTIVE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
CACHE_MAX_AGE_HOURS = 2   # CelesTrak throttles repeated downloads

SAFETY_DISTANCE_KM = 100.0
CRITICAL_DISTANCE_KM = 20.0

FORECAST_HOURS = 72
STEP_MINUTES = 10