import numpy as np, pandas as pd
from scipy import stats

def window_total(df, end, days=7):
    w = df[(df.date > end - pd.Timedelta(days=days)) & (df.date <= end)].rain_mm
    return float(w.sum()) if w.notna().sum() == days else np.nan

def baseline_totals(df, end, days, y0, y1):
    out = []
    for y in range(y0, y1 + 1):
        try:
            e = end.replace(year=y)
        except ValueError:
            e = end.replace(year=y, day=28)
        t = window_total(df, pd.Timestamp(e), days)
        if not np.isnan(t):
            out.append(t)
    return np.array(out)

def anomaly(total, base):
    if np.isnan(total) or len(base) < 10:
        return None
    mean = base.mean()
    return dict(mean=float(mean), pct=float((total - mean) / mean * 100) if mean > 0 else None,
                percentile=float(stats.percentileofscore(base, total)), n=len(base))

def seasonal_totals(df, m0=6, m1=9):
    d = df[(df.date.dt.month >= m0) & (df.date.dt.month <= m1)].copy()
    g = d.groupby(d.date.dt.year).rain_mm
    cov = g.apply(lambda s: s.notna().mean())
    return pd.DataFrame({"year": g.sum().index, "total_mm": g.sum().values, "coverage": cov.values})

def monthly(df):
    m = df.set_index("date").rain_mm.resample("MS").sum(min_count=20)
    return m.reset_index().rename(columns={"rain_mm": "mm"})

def mann_kendall(y, alpha=0.05):
    y = np.asarray(y, float); n = len(y)
    if n < 4:
        return None
    s = sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n))
    var = n * (n - 1) * (2 * n + 5) / 18          # no tie correction (documented limitation)
    z = (s - np.sign(s)) / np.sqrt(var) if s != 0 else 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    slope = np.median([(y[j] - y[i]) / (j - i) for i in range(n - 1) for j in range(i + 1, n)])
    trend = "no significant trend" if p >= alpha else ("increasing" if z > 0 else "decreasing")
    return dict(n=n, S=float(s), z=float(z), p=float(p), sen_slope=float(slope), trend=trend)
