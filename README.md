# ResilientEarth
Earth System Intelligence for a Resilient Future: Streamlit dashboard for rainfall, flood and agricultural intelligence (Indus Basin pilot).

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
Toggle **Demo Mode** in the sidebar for labelled synthetic sample data. Live rainfall uses NASA POWER (no login).

## Deploy
Push to GitHub, then create the app on Streamlit Community Cloud (main file `app.py`). Add secrets in the app settings; never commit `.streamlit/secrets.toml`.

## Official bulletins (controlled import)
Create `data/reference/official_bulletins.csv`: `date,district,status,source_name,source_url`.

## Status
Done: layout, geography filters, evidence labels, POWER rainfall, anomalies, Mann-Kendall/Sen, Demo Mode, tests.
Next: district boundaries, IMERG, MODIS extraction, LANCE flood extent, exposure, CI.
Principles: evidence before prediction, validation before probability, transparency before claims.
