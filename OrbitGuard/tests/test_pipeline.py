import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.sgp4_propagator import load_satellites, make_times, propagate  # noqa: E402
from src.engine.collision_risk import CollisionRiskEngine  # noqa: E402

ISS = {
    "OBJECT_NAME": "ISS (ZARYA)", "OBJECT_ID": "1998-067A", "NORAD_CAT_ID": 25544, "EPOCH": "2008-09-20T12:25:40.104192",
    "MEAN_MOTION": 15.72125391, "ECCENTRICITY": 0.0006703, "INCLINATION": 51.6416,
    "RA_OF_ASC_NODE": 247.4627, "ARG_OF_PERICENTER": 130.5360, "MEAN_ANOMALY": 325.0288,
    "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U", "ELEMENT_SET_NO": 292, "REV_AT_EPOCH": 56353,
    "BSTAR": -0.000011606, "MEAN_MOTION_DOT": -0.00002182, "MEAN_MOTION_DDOT": 0,
}


def test_end_to_end(tmp_path):
    twin = copy.deepcopy(ISS)
    twin.update(NORAD_CAT_ID=99999, OBJECT_NAME="TWIN", MEAN_ANOMALY=325.0298)  # ~1 km apart
    f = tmp_path / "sats.json"
    f.write_text(json.dumps([ISS, twin]))
    sats, meta = load_satellites(f)
    assert len(sats) == 2
    t0 = datetime(2008, 9, 20, 12, 25, 40, tzinfo=timezone.utc)
    states = propagate(sats, meta, make_times(t0, hours=0, step_minutes=1)[:1])
    df = next(iter(states.values()))
    assert (df["error_code"] == 0).all()
    with CollisionRiskEngine(tmp_path / "t.duckdb") as eng:
        assert eng.evaluate_conjunctions(df, t0) == 1
