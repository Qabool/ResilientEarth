import streamlit as st
from data_connectors import nasa_power, nasa_modis, official_bulletins
from services import sample
from evidence import now_utc

@st.cache_data(ttl=6 * 3600, show_spinner="Retrieving rainfall...")
def get_rainfall(district, coords, demo):
    """Returns (DataFrame | None, meta). On failure returns None, never a fabricated value."""
    if demo:
        return sample.rainfall(district), dict(source="SAMPLE (synthetic)", cls="Sample data", retrieved=now_utc())
    try:
        df = nasa_power.fetch_rainfall(*coords)
        return df, dict(source="NASA POWER daily PRECTOTCORR", cls="Observation", retrieved=now_utc())
    except Exception as e:
        return None, dict(source="NASA POWER", cls="Observation", error=type(e).__name__)

@st.cache_data(ttl=6 * 3600)
def get_ndvi(district, demo):
    if demo:
        return sample.ndvi(district), dict(source="SAMPLE (synthetic)", cls="Sample data")
    df = nasa_modis.load_ndvi(district)
    return df, dict(source="MODIS MOD13Q1.061 (processed)", cls="Observation")

def get_flood(district, demo):
    if demo:
        return dict(status=sample.FLOOD["status"], source="SAMPLE", cls="Sample data", exposed_ha=sample.FLOOD["exposed_ha"])
    b = official_bulletins.latest_status(district)
    return None if b is None else dict(status=b["status"], source=f'{b["source_name"]} ({str(b["date"])[:10]})', cls="Official bulletin (imported)")
