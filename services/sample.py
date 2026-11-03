"""Synthetic SAMPLE data for Demo Mode only. Never mixed with live values."""
import zlib, numpy as np, pandas as pd

def rainfall(district):
    rng = np.random.default_rng(zlib.crc32(district.encode()))
    dates = pd.date_range("2001-01-01", pd.Timestamp.today().normalize())
    season = np.exp(-((dates.dayofyear.values - 215) / 35.0) ** 2)
    wet = rng.random(len(dates)) < (0.04 + 0.5 * season)
    amt = rng.gamma(0.8, 1.0, len(dates)) * (3 + 12 * season) * wet
    return pd.DataFrame({"date": dates, "rain_mm": amt})

def ndvi(district):
    rng = np.random.default_rng(zlib.crc32(district.encode()) + 1)
    d = pd.date_range("2001-01-01", pd.Timestamp.today().normalize(), freq="16D")
    v = 0.40 + 0.22 * np.sin((d.dayofyear.values - 80) / 365 * 2 * np.pi) + rng.normal(0, 0.03, len(d))
    return pd.DataFrame({"date": d, "ndvi": v.clip(0.05, 0.9)})

FLOOD = {"status": "Normal (sample)", "exposed_ha": 12000}
