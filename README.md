# ResilientEarth v0.2

**Earth System Intelligence for a Resilient Future** — an interactive Streamlit prototype for rainfall, flood-information discovery and agricultural-condition monitoring in the Indus Basin pilot (Punjab and Sindh, Pakistan).

## What's new in v0.2
- Interactive rainfall explorer with date range, daily/monthly/monsoon views and CSV export.
- District comparison (2–5 districts) using cached NASA POWER point queries.
- Monsoon scenario lab: transparent what-if rainfall multiplier; explicitly not a forecast or flood probability.
- On-demand Serper-powered Earth intelligence search using `SERPER_API_KEY`.
- Improved completeness rules: incomplete monthly/monsoon totals are withheld rather than shown as partial totals.
- Mann–Kendall tie correction and Sen slope based on actual year spacing.
- Clearer source classifications and provenance metadata.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit deployment
Deploy `app.py` from GitHub on Streamlit Community Cloud. Add keys in **App settings → Secrets**:
```toml
NASA_API_KEY = "your_nasa_api_key"
SERPER_API_KEY = "your_serper_api_key"
```
NASA POWER's public daily API does not require `NASA_API_KEY`; the key is retained for future NASA Open APIs that require it. Earthdata credentials are not needed for the current POWER connector. Never commit secrets.

## Data modes and limitations
- Live rainfall: NASA POWER `PRECTOTCORR`, queried at the district bounding-box centre. This is a point representation, not an area-weighted district average.
- Demo mode: deterministic synthetic data, clearly labelled; never mix with live data.
- MODIS NDVI/EVI: requires preprocessed district Parquet files at `data/processed/ndvi_<district_slug>.parquet` with at least `date` and `ndvi` columns.
- Official PMD/FFD bulletins: controlled CSV import at `data/reference/official_bulletins.csv` with `date,district,status,source_name,source_url`.
- GPM IMERG spatial aggregation, LANCE flood extent, and validated flood/yield models are not yet implemented.
- Serper results are discovery leads, not verified measurements or official warnings.

## Scientific safeguards
- Missing data are not converted to zero.
- Seven-day accumulations require complete daily coverage.
- Monthly and monsoon totals below the documented coverage threshold are withheld.
- The scenario lab is a mathematical what-if, not a forecast, hydrological model or probability estimate.
- NDVI is not yield; exposed cropland is not confirmed crop loss.
- Follow PMD, FFD and disaster-management authorities for operational warnings.

## Tests
```bash
pytest -q
```

## Project principles
Evidence before prediction · Validation before probability · Transparency before claims.
