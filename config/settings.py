import json
from pathlib import Path

PAGES = [
    "Overview", "Rainfall Explorer", "District Compare", "Monsoon Scenario Lab",
    "Flood Intelligence", "Agricultural Impact", "Earth Intelligence Search", "Data & Methodology",
]
GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "reference" / "districts_punjab_sindh.geojson"


def _bbox(c, acc=None):
    acc = acc or [999, 999, -999, -999]
    if isinstance(c[0], list):
        for x in c:
            _bbox(x, acc)
    else:
        acc[0], acc[1], acc[2], acc[3] = min(acc[0], c[0]), min(acc[1], c[1]), max(acc[2], c[0]), max(acc[3], c[1])
    return acc


def load_geo():
    """Load GADM-derived pilot boundaries; verify administrative vintage before official use."""
    gj = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    districts = {}
    for feature in gj["features"]:
        bounds = _bbox(feature["geometry"]["coordinates"])
        province = feature["properties"]["province"]
        district = feature["properties"]["district"]
        # Bounding-box centre is only a point-query approximation, not a district mean.
        districts.setdefault(province, {})[district] = ((bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2)
    return gj, {p: dict(sorted(v.items())) for p, v in sorted(districts.items())}


GEOJSON, DISTRICTS = load_geo()
BASE0, BASE1 = 2001, 2020  # Proposed reference period; confirm suitability per dataset.
MONSOON = (6, 9)
MIN_TREND_YEARS, MIN_COVERAGE = 20, 0.80
