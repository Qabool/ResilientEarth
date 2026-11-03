"""MODIS MOD13Q1.061 NDVI/EVI connector: TODO (Phase 2).
Needs Earthdata Login (st.secrets['earthdata']). Run extraction offline to district Parquet
(data/processed/ndvi_<district>.parquet with columns date, ndvi, evi) and load it here."""
import os, pandas as pd

def load_ndvi(district):
    p = f"data/processed/ndvi_{district.lower().replace(' ', '_')}.parquet"
    return pd.read_parquet(p) if os.path.exists(p) else None
