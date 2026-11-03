import numpy as np, pandas as pd
from analytics import rainfall as rf
def test_mk_increasing():
    r = rf.mann_kendall(np.arange(25) + np.random.default_rng(0).normal(0, .1, 25))
    assert r["trend"] == "increasing" and r["sen_slope"] > 0.8
def test_mk_flat():
    assert rf.mann_kendall(np.random.default_rng(1).normal(0, 1, 25))["trend"] == "no significant trend"
def test_missing_not_zero():
    d = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=7), "rain_mm": [1, 1, np.nan, 1, 1, 1, 1]})
    assert np.isnan(rf.window_total(d, d.date.max(), 7))
def test_anomaly():
    a = rf.anomaly(30.0, np.full(15, 20.0)); assert round(a["pct"]) == 50
