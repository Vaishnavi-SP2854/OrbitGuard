import sys
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.storage.db_handler import db_exists, get_alerts, alert_counts  # noqa: E402

app = FastAPI(title="OrbitGuard Space Debris & Conjunction API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "online", "system": "OrbitGuard Engine", "db_exists": db_exists()}


def _guard():
    if not db_exists():
        raise HTTPException(404, "No database yet. Run: python run_all.py")


@app.get("/alerts/latest")
def latest_alerts(limit: int = 50, risk_level: str | None = None):
    _guard()
    try:
        df = get_alerts(limit, risk_level)
        df["timestamp"] = df["timestamp"].astype(str)
        return {"count": len(df), "alerts": df.to_dict(orient="records")}
    except duckdb.IOException as e:
        raise HTTPException(503, f"Database is locked by another process: {e}")


@app.get("/alerts/summary")
def summary():
    _guard()
    return alert_counts()
