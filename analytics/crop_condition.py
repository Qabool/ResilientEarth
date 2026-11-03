import numpy as np
def ndvi_anomaly(df, y0, y1):
    """Latest NDVI vs mean of same calendar month in the baseline years."""
    d = df.dropna(subset=["ndvi"]); last = d.iloc[-1]
    b = d[(d.date.dt.month == last.date.month) & d.date.dt.year.between(y0, y1)].ndvi
    if len(b) < 10:
        return None
    return dict(latest=float(last.ndvi), date=last.date, baseline=float(b.mean()),
                pct=float((last.ndvi - b.mean()) / b.mean() * 100))
