"""SGP4 propagation of CelesTrak OMM/JSON records into ECI state vectors."""
import json
import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sgp4 import omm
from sgp4.api import Satrec, SatrecArray, jday


def load_satellites(json_path):
    """Return (list[Satrec], list[(norad_id, name)]). Bad records are skipped."""
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    sats, meta = [], []
    for rec in records:
        try:
            sat = Satrec()
            omm.initialize(sat, rec)
            sats.append(sat)
            meta.append((int(rec["NORAD_CAT_ID"]), str(rec.get("OBJECT_NAME", ""))))
        except Exception:  # noqa: BLE001 - skip malformed record
            continue
    return sats, meta


def _julian_arrays(times):
    jd, fr = zip(*[jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond * 1e-6)
                   for t in times])
    return np.array(jd), np.array(fr)


def make_times(start=None, hours=72, step_minutes=10):
    start = start or datetime.now(timezone.utc)
    n = int(hours * 60 / step_minutes) + 1
    return [start + timedelta(minutes=step_minutes * i) for i in range(n)]


def propagate(sats, meta, times):
    """Propagate all satellites at all times.

    Returns dict {time: DataFrame[norad_id,name,x,y,z,vx,vy,vz,error_code]} (km, km/s).
    """
    jd, fr = _julian_arrays(times)
    e, r, v = SatrecArray(sats).sgp4(jd, fr)  # e:(S,T) r,v:(S,T,3)
    ids = np.array([m[0] for m in meta])
    names = np.array([m[1] for m in meta])
    out = {}
    for t_idx, t in enumerate(times):
        out[t] = pd.DataFrame({
            "norad_id": ids, "name": names,
            "x": r[:, t_idx, 0], "y": r[:, t_idx, 1], "z": r[:, t_idx, 2],
            "vx": v[:, t_idx, 0], "vy": v[:, t_idx, 1], "vz": v[:, t_idx, 2],
            "error_code": e[:, t_idx].astype(int),
        })
    return out


def eci_to_latlon_alt(df):
    """Approximate geodetic lat/lon/alt from TEME positions (good enough for display)."""
    now = datetime.now(timezone.utc)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
    d = (jd - 2451545.0) + fr
    gmst = math.radians((280.46061837 + 360.98564736629 * d) % 360.0)
    x, y, z = df["x"].to_numpy(), df["y"].to_numpy(), df["z"].to_numpy()
    lon = np.degrees(np.arctan2(y, x) - gmst)
    lon = (lon + 180) % 360 - 180
    rxy = np.hypot(x, y)
    lat = np.degrees(np.arctan2(z, rxy))
    alt_km = np.sqrt(x**2 + y**2 + z**2) - 6371.0
    return lat, lon, alt_km
