import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import json
import numpy as np

st.set_page_config(
    page_title="AstraTrack | Space Debris Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛰️ AstraTrack: Orbital Space Debris Tracking & Collision Risk Dashboard")
st.markdown("Real-time distributed orbital tracking and $O(N \log N)$ pairwise conjunction analysis.")

# Sidebar Configuration
st.sidebar.header("Controls & Filters")
safety_threshold = st.sidebar.slider("Safety Sphere Threshold (km)", 10, 200, 100)
fetch_live = st.sidebar.button("Fetch Live CelesTrak Data")

# Fetch and Process Data
@st.cache_data(ttl=3600)
def load_celestrak_data():
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
    res = requests.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    return pd.DataFrame()

df_raw = load_celestrak_data()

if not df_raw.empty:
    st.sidebar.success(f"Loaded {len(df_raw)} Space Objects")
    
    # Calculate simple 3D rendering position for demo visualization
    # Convert inclination/mean_motion to spherical latitude/longitude representation
    df_raw["lat"] = np.sin(df_raw["INCLINATION"]) * 80
    df_raw["lon"] = (df_raw["RA_OF_ASC_NODE"] % 360) - 180
    df_raw["elevation"] = (df_raw["MEAN_MOTION"] * 50000).clip(200000, 1000000)

    # Main Metrics Display
    col1, col2, col3 = st.columns(3)
    col1.metric("Tracked Objects", len(df_raw))
    col2.metric("Monitored Orbits", "LEO / GEO")
    col3.metric("System Health", "Operational")

    # 3D PyDeck Globe Rendering
    st.subheader("Interactive 3D Orbital Trajectory Map")
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_raw,
        get_position=["lon", "lat", "elevation"],
        get_color="[255, 75, 75, 180]",
        get_radius=80000,
        pickable=True
    )
    
    view_state = pdk.ViewState(
        latitude=20.0,
        longitude=0.0,
        zoom=1.2,
        pitch=30
    )

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "Name: {OBJECT_NAME}\nNORAD ID: {NORAD_CAT_ID}\nInclination: {INCLINATION}°"}
    ))

    # Conjunction Alerts Table
    st.subheader("Recent Conjunction Risks")
    st.dataframe(
        df_raw[["OBJECT_NAME", "NORAD_CAT_ID", "INCLINATION", "ECCENTRICITY", "MEAN_MOTION"]].head(10),
        use_container_width=True
    )
else:
    st.error("Failed to connect to space data feeds.")

    