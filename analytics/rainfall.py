"""Rainfall analytics with explicit completeness handling."""
import numpy as np
import pandas as pd
from scipy import stats


def window_total(df, end, days=7, min_coverage=1.0):
    end = pd.Timestamp(end).normalize()
    start = end - pd.Timedelta(days=days - 1)
    w = df.loc[df.date.between(start, end), "rain_mm"]
    expected = days
    coverage = float(w.notna().sum() / expected) if expected else 0.0
    if coverage < min_coverage or w.notna().sum() == 0:
        return np.nan
    return float(w.sum(min_count=1))


def baseline_totals(df, end, days, y0, y1, min_coverage=1.0):
    out = []
    end = pd.Timestamp(end)
    for year in range(y0, y1 + 1):
        try:
            candidate = end.replace(year=year)
        except ValueError:
            candidate = end.replace(year=year, day=28)
        value = window_total(df, candidate, days, min_coverage)
        if np.isfinite(value):
            out.append(value)
    return np.asarray(out, dtype=float)


def anomaly(total, base):
    base = np.asarray(base, dtype=float)
    base = base[np.isfinite(base)]
    if not np.isfinite(total) or len(base) < 5:
        return None
    mean = float(base.mean())
    return {
        "mean": mean,
        "pct": float((total - mean) / mean * 100) if mean > 0 else None,
        "percentile": float(stats.percentileofscore(base, total, kind="mean")),
        "n": int(len(base)),
    }


def seasonal_totals(df, m0=6, m1=9, min_coverage=0.80):
    """Return annual season totals; incomplete seasons remain NaN, not partial totals."""
    d = df.loc[df.date.dt.month.between(m0, m1)].copy()
    if d.empty:
        return pd.DataFrame(columns=["year", "total_mm", "coverage", "complete"])
    rows = []
    for year, group in d.groupby(d.date.dt.year):
        start = pd.Timestamp(year=int(year), month=m0, day=1)
        end = pd.Timestamp(year=int(year), month=m1, day=1) + pd.offsets.MonthEnd(0)
        expected = len(pd.date_range(start, end, freq="D"))
        observed = int(group.rain_mm.notna().sum())
        coverage = observed / expected if expected else 0.0
        complete = coverage >= min_coverage
        total = float(group.rain_mm.sum(min_count=1)) if complete else np.nan
        rows.append({"year": int(year), "total_mm": total, "coverage": coverage, "complete": complete})
    return pd.DataFrame(rows)


def monthly(df, min_coverage=0.80):
    """Monthly totals are only emitted when the requested coverage is achieved."""
    x = df.set_index("date").sort_index().rain_mm
    totals = x.resample("MS").sum(min_count=1)
    counts = x.resample("MS").count()
    month_starts = totals.index
    expected = pd.Series([pd.Period(m, freq="M").days_in_month for m in month_starts], index=month_starts)
    coverage = counts / expected.replace(0, np.nan)
    totals[coverage < min_coverage] = np.nan
    return pd.DataFrame({"date": totals.index, "mm": totals.values, "coverage": coverage.values})


def mann_kendall(y, years=None, alpha=0.05):
    """Two-sided Mann-Kendall with tie correction; Sen slope uses actual year spacing."""
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(y)
    y = y[mask]
    if years is None:
        x = np.arange(len(y), dtype=float)
    else:
        x = np.asarray(years, dtype=float)[mask]
    n = len(y)
    if n < 4:
        return None
    s = float(sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n)))
    _, counts = np.unique(y, return_counts=True)
    tie_term = sum(int(t) * (int(t) - 1) * (2 * int(t) + 5) for t in counts if t > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18
    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = float(2 * (1 - stats.norm.cdf(abs(z))))
    slopes = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(n - 1) for j in range(i + 1, n) if x[j] != x[i]]
    slope = float(np.median(slopes)) if slopes else np.nan
    trend = "no significant trend" if p >= alpha else ("increasing" if z > 0 else "decreasing")
    return {"n": n, "S": s, "z": float(z), "p": p, "sen_slope": slope, "trend": trend}
