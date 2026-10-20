import os
from pathlib import Path

try:  # optional: load overrides from a .env file if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "astratrack.duckdb"

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- Ingestion ---------------------------------------------------------------
CELESTRAK_GROUP = os.getenv("CELESTRAK_GROUP", "active")
CELESTRAK_ACTIVE_URL = (
    f"https://celestrak.org/NORAD/elements/gp.php?GROUP={CELESTRAK_GROUP}&FORMAT=json"
)
RAW_FILE = DATA_RAW_DIR / f"{CELESTRAK_GROUP}.json"
# CelesTrak updates data every few hours and throttles repeated downloads.
CACHE_MAX_AGE_HOURS = float(os.getenv("CACHE_MAX_AGE_HOURS", "2"))

# --- Propagation -------------------------------------------------------------
FORECAST_HOURS = int(os.getenv("FORECAST_HOURS", "72"))
STEP_MINUTES = int(os.getenv("STEP_MINUTES", "10"))

# --- Conjunction screening ---------------------------------------------------
SAFETY_DISTANCE_KM = float(os.getenv("SAFETY_DISTANCE_KM", "100"))  # WARNING threshold
CRITICAL_DISTANCE_KM = float(os.getenv("CRITICAL_DISTANCE_KM", "20"))