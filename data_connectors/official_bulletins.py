"""Controlled import for PMD/FFD bulletins (no stable API).
Maintain data/reference/official_bulletins.csv with columns:
date,district,status,source_name,source_url"""
import os, pandas as pd
PATH = "data/reference/official_bulletins.csv"

def latest_status(district):
    if not os.path.exists(PATH):
        return None
    df = pd.read_csv(PATH, parse_dates=["date"])
    df = df[df.district.str.lower().isin([district.lower(), "all"])].sort_values("date")
    return None if df.empty else df.iloc[-1].to_dict()
