import numpy as np
import pandas as pd
from analytics import rainfall as rf


def test_window_total_requires_complete_window():
    d = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=7), "rain_mm": [1, 2, 3, 4, 5, 6, 7]})
    assert rf.window_total(d, pd.Timestamp("2024-01-07"), 7) == 28
    d.loc[0, "rain_mm"] = np.nan
    assert np.isnan(rf.window_total(d, pd.Timestamp("2024-01-07"), 7))


def test_seasonal_totals_hides_incomplete_season():
    dates = pd.date_range("2020-06-01", "2020-09-30")
    df = pd.DataFrame({"date": dates, "rain_mm": 1.0})
    df.loc[0:60, "rain_mm"] = np.nan
    result = rf.seasonal_totals(df, min_coverage=.8)
    assert not bool(result.iloc[0].complete)
    assert np.isnan(result.iloc[0].total_mm)


def test_mann_kendall_tie_corrected_and_slope_uses_years():
    result = rf.mann_kendall([1, 1, 2, 3, 4], years=[2000, 2001, 2002, 2003, 2004])
    assert result is not None
    assert result["sen_slope"] > 0
    assert result["trend"] == "increasing"


def test_mann_kendall_short_series():
    assert rf.mann_kendall([1, 2, 3]) is None
