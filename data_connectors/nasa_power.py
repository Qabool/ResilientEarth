"""NASA POWER daily API (no Earthdata login; optional api.nasa.gov key not required)."""
import datetime as dt, numpy as np, pandas as pd, requests
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def fetch_rainfall(lat, lon, start="20010101", end=None, timeout=60):
    end = end or dt.date.today().strftime("%Y%m%d")
    params = dict(parameters="PRECTOTCORR", community="AG", latitude=lat, longitude=lon,
                  start=start, end=end, format="JSON")
    r = requests.get(URL, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()["properties"]["parameter"]["PRECTOTCORR"]
    df = pd.DataFrame({"date": pd.to_datetime(list(data), format="%Y%m%d"),
                       "rain_mm": list(data.values())})
    df["rain_mm"] = df["rain_mm"].replace(-999, np.nan)   # missing stays missing, never zero
    return df.sort_values("date").reset_index(drop=True)
