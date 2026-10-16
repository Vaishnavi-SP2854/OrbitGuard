"""Small helper for reading conjunction alerts from DuckDB (used by the API and dashboard)."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import DB_PATH  # noqa: E402


def db_exists() -> bool:
    return Path(DB_PATH).exists()


def get_alerts(limit: int = 50, risk_level: str | None = None) -> pd.DataFrame:
    """Closest conjunctions first. risk_level: 'CRITICAL' or 'WARNING' (optional)."""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        if risk_level:
            return conn.execute(
                "SELECT * FROM conjunction_alerts WHERE risk_level = ? ORDER BY distance_km LIMIT ?",
                [risk_level.upper(), limit]).fetchdf()
        return conn.execute(
            "SELECT * FROM conjunction_alerts ORDER BY distance_km LIMIT ?", [limit]).fetchdf()
    finally:
        conn.close()


def alert_counts() -> dict:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows = conn.execute(
            "SELECT risk_level, COUNT(*) FROM conjunction_alerts GROUP BY risk_level").fetchall()
        return {k: v for k, v in rows}
    finally:
        conn.close()
