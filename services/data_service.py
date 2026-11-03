import streamlit as st
from data_connectors import nasa_power, nasa_modis, official_bulletins
from services import sample
from evidence import now_utc

@st.cache_data(ttl=6 * 3600, show_spinner="Retrieving NASA POWER rainfall...")
def get_rainfall(district, coords, demo):
    """Returns (DataFrame | None, metadata); never fabricates live values."""
    if demo:
        return sample.rainfall(district), dict(source="SAMPLE (synthetic)", cls="Sample data", retrieved=now_utc(),
                                               method="Deterministic synthetic generator", quality="Illustrative only")
    try:
        df = nasa_power.fetch_rainfall(*coords)
        return df, dict(source="NASA POWER daily PRECTOTCORR", cls="Gridded meteorological estimate",
                        retrieved=now_utc(), method="Daily point query at district bounding-box centre",
                        quality="Point representation; not district-wide average")
    except Exception as e:
        return None, dict(source="NASA POWER", cls="Unavailable", retrieved=now_utc(), error=f"{type(e).__name__}: {e}")

@st.cache_data(ttl=6 * 3600)
def get_ndvi(district, demo):
    if demo:
        return sample.ndvi(district), dict(source="SAMPLE (synthetic)", cls="Sample data", retrieved=now_utc())
    try:
        df = nasa_modis.load_ndvi(district)
        return df, dict(source="MODIS MOD13Q1.061 (processed)", cls="Satellite observation", retrieved=now_utc())
    except Exception:
        return None, dict(source="MODIS MOD13Q1.061", cls="Unavailable", retrieved=now_utc())

def get_flood(district, demo):
    if demo:
        return dict(status=sample.FLOOD["status"], source="SAMPLE", cls="Sample data", exposed_ha=sample.FLOOD["exposed_ha"])
    try:
        b = official_bulletins.latest_status(district)
        return None if b is None else dict(status=b["status"], source=f'{b["source_name"]} ({str(b["date"])[:10]})', cls="Official bulletin (imported)")
    except Exception:
        return None
