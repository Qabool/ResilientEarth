PAGES = ["Overview", "Rainfall Trends", "Flood Intelligence", "Agricultural Impact",
         "District Investigation", "Data & Methodology"]
# (lat, lon) district centroids for the pilot; replace with GeoJSON boundaries in data/reference/
DISTRICTS = {
    "Punjab": {"Muzaffargarh": (30.07, 71.19), "Multan": (30.20, 71.47), "Lahore": (31.55, 74.34),
               "Faisalabad": (31.42, 73.08), "Rahim Yar Khan": (28.42, 70.30)},
    "Sindh": {"Sukkur": (27.71, 68.86), "Larkana": (27.56, 68.22), "Hyderabad": (25.39, 68.37)},
}
BASE0, BASE1 = 2001, 2020      # reference period for anomalies (proposed; confirm per dataset)
MONSOON = (6, 9)               # June-September
MIN_TREND_YEARS, MIN_COVERAGE = 20, 0.80
