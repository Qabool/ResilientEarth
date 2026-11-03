import json
from pathlib import Path
PAGES = ["Overview", "Rainfall Trends", "Flood Intelligence", "Agricultural Impact",
         "District Investigation", "Data & Methodology"]
GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "reference" / "districts_punjab_sindh.geojson"

def _bbox(c, acc=None):
    acc = acc or [999, 999, -999, -999]
    if isinstance(c[0], list):
        for x in c: _bbox(x, acc)
    else:
        acc[0], acc[1], acc[2], acc[3] = min(acc[0], c[0]), min(acc[1], c[1]), max(acc[2], c[0]), max(acc[3], c[1])
    return acc

def load_geo():
    """District polygons (GADM-derived, via PakData/GISData; older boundaries, verify before official use)."""
    gj = json.loads(GEOJSON_PATH.read_text())
    districts = {}
    for f in gj["features"]:
        b = _bbox(f["geometry"]["coordinates"])
        # (lat, lon) = bounding-box centre: an approximation used to query point-based APIs
        districts.setdefault(f["properties"]["province"], {})[f["properties"]["district"]] = ((b[1] + b[3]) / 2, (b[0] + b[2]) / 2)
    return gj, {p: dict(sorted(v.items())) for p, v in sorted(districts.items())}

GEOJSON, DISTRICTS = load_geo()
BASE0, BASE1 = 2001, 2020      # reference period for anomalies (proposed; confirm per dataset)
MONSOON = (6, 9)
MIN_TREND_YEARS, MIN_COVERAGE = 20, 0.80
