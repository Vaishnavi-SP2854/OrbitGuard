import sys
from pathlib import Path

import duckdb
import pandas as pd
import pydeck as pdk
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import DB_PATH, RAW_FILE  # noqa: E402
from src.ingestion.celestrak_ingest import run_ingestion  # noqa: E402
from src.engine.sgp4_propagator import load_satellites, make_times, propagate, eci_to_latlon_alt  # noqa: E402

st.set_page_config(page_title="OrbitGuard | Space Debris Engine", layout="wide")
st.title("🛰️ OrbitGuard: Orbital Debris Tracking & Collision Risk Dashboard")
st.markdown(r"Orbital tracking with SGP4 and $O(N \log N)$ KD-tree conjunction screening.")

st.sidebar.header("Controls")
if st.sidebar.button("Re-download CelesTrak data"):
    run_ingestion(force=True)
    st.cache_data.clear()


@st.cache_data(ttl=3600)
def load_positions():
    path = str(RAW_FILE) if Path(RAW_FILE).exists() else run_ingestion()
    if not path:
        return pd.DataFrame()
    sats, meta = load_satellites(path)
    states = propagate(sats, meta, make_times(hours=0, step_minutes=1)[:1])
    df = next(iter(states.values()))
    df = df[df["error_code"] == 0].copy()
    df["lat"], df["lon"], df["alt_km"] = eci_to_latlon_alt(df)
    return df


df = load_positions()
if df.empty:
    st.error("No orbital data. Run `python -m src.ingestion.celestrak_ingest` first (needs internet).")
    st.stop()

c1, c2 = st.columns(2)
c1.metric("Tracked objects", len(df))
c2.metric("Mean altitude (km)", f"{df['alt_km'].mean():.0f}")

st.subheader("Current satellite positions")
layer = pdk.Layer("ScatterplotLayer", data=df, get_position=["lon", "lat"],
                  get_fill_color=[255, 75, 75, 180], get_radius=60000, pickable=True)
st.pydeck_chart(pdk.Deck(
    map_style=None,  # a "mapbox://" style needs an API token and shows blank without one
    initial_view_state=pdk.ViewState(latitude=20, longitude=0, zoom=1, pitch=0),
    layers=[layer], tooltip={"text": "{name}\nNORAD {norad_id}\nAlt {alt_km} km"}))

st.subheader("Conjunction alerts (from pipeline)")
if Path(DB_PATH).exists():
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        alerts = conn.execute("SELECT * FROM conjunction_alerts ORDER BY distance_km LIMIT 100").fetchdf()
        conn.close()
        st.dataframe(alerts, use_container_width=True)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Could not read alerts (is the pipeline still running?): {e}")
else:
    st.info("No alerts yet. Run `python -m src.run_pipeline`.")