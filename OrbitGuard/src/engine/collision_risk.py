"""KD-tree conjunction screening, results stored in DuckDB."""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import DB_PATH, SAFETY_DISTANCE_KM, CRITICAL_DISTANCE_KM  # noqa: E402


class CollisionRiskEngine:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conjunction_alerts (
                timestamp TIMESTAMP,
                sat1_id INTEGER, sat1_name VARCHAR,
                sat2_id INTEGER, sat2_name VARCHAR,
                distance_km DOUBLE, risk_level VARCHAR,
                PRIMARY KEY (timestamp, sat1_id, sat2_id)
            )""")

    def evaluate_conjunctions(self, df_states: pd.DataFrame, timestamp) -> int:
        valid = df_states[df_states["error_code"] == 0].reset_index(drop=True)
        if len(valid) < 2:
            return 0
        coords = valid[["x", "y", "z"]].to_numpy()
        pairs = np.array(sorted(KDTree(coords).query_pairs(r=SAFETY_DISTANCE_KM)))
        if pairs.size == 0:
            return 0
        i, j = pairs[:, 0], pairs[:, 1]
        dist = np.linalg.norm(coords[i] - coords[j], axis=1)
        a, b = valid.iloc[i], valid.iloc[j]
        ts = pd.Timestamp(timestamp)
        if ts.tzinfo:
            ts = ts.tz_localize(None)
        df = pd.DataFrame({
            "timestamp": ts,
            "sat1_id": a["norad_id"].to_numpy(), "sat1_name": a["name"].to_numpy(),
            "sat2_id": b["norad_id"].to_numpy(), "sat2_name": b["name"].to_numpy(),
            "distance_km": dist,
            "risk_level": np.where(dist <= CRITICAL_DISTANCE_KM, "CRITICAL", "WARNING"),
        })
        self.conn.register("df_temp", df)
        self.conn.execute("INSERT OR REPLACE INTO conjunction_alerts SELECT * FROM df_temp")
        self.conn.unregister("df_temp")
        return len(df)

    def close(self):
        # DuckDB allows only ONE writer process; close so the API/dashboard can open the file.
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
