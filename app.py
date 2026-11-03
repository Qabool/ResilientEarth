import datetime as dt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.settings import PAGES, DISTRICTS, GEOJSON, BASE0, BASE1, MIN_TREND_YEARS, MIN_COVERAGE
from services import data_service as ds
from analytics import rainfall as rf, crop_condition as cc
from components.ui import inject_css, card
from data_connectors.serper_search import search as serper_search

st.set_page_config(page_title="ResilientEarth | Earth System Intelligence", page_icon="🌍", layout="wide")
inject_css()

# --- Shared helpers ---
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

def fmt_mm(value):
    return f"{value:,.1f} mm" if value is not None and pd.notna(value) else "Unavailable"

def safe_period(df, start, end):
    return df.loc[df.date.between(pd.Timestamp(start), pd.Timestamp(end))].copy()

def make_rain_chart(df, title="Daily rainfall"):
    f = px.area(df, x="date", y="rain_mm", title=title, labels={"rain_mm": "Rainfall (mm)", "date": "Date"})
    f.update_traces(line=dict(width=1.5))
    f.update_layout(margin=dict(l=5, r=5, t=45, b=5), hovermode="x unified")
    return f

def latest_summary(rain, end, days, y0, y1):
    total = rf.window_total(rain, end, days, min_coverage=1.0)
    base = rf.baseline_totals(rain, end, days, y0, y1, min_coverage=1.0)
    return total, rf.anomaly(total, base)

def get_selected_data(province, district, demo):
    coords = DISTRICTS[province][district]
    rain, rmeta = ds.get_rainfall(district, coords, demo)
    ndvi, nmeta = ds.get_ndvi(district, demo)
    flood = ds.get_flood(district, demo)
    return rain, rmeta, ndvi, nmeta, flood

# --- Sidebar ---
with st.sidebar:
    st.markdown("# 🌍 ResilientEarth")
    st.caption("Explore Earth · Understand change · Build resilience")
    page = st.radio("Workspace", PAGES, label_visibility="collapsed")
    st.divider()
    province = st.selectbox("Pilot province", list(DISTRICTS))
    district_names = list(DISTRICTS[province])
    default_district = "Muzaffargarh" if "Muzaffargarh" in district_names else district_names[0]
    district = st.selectbox("District", district_names, index=district_names.index(default_district))
    demo = st.toggle("Demo mode · synthetic data", value=False)
    st.caption("Live rainfall uses NASA POWER. Demo values are synthetic.")
    if st.button("↻ Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

coords = DISTRICTS[province][district]
rain, rmeta, ndvi, nmeta, flood = get_selected_data(province, district, demo)

# --- Header ---
head_l, head_r = st.columns([4, 1])
with head_l:
    st.title("ResilientEarth")
    st.caption(f"Earth System Intelligence for a Resilient Future  ·  {district}, {province}, Pakistan")
with head_r:
    st.metric("Data mode", "DEMO" if demo else "LIVE / CONNECTED")
if demo:
    st.warning("Demo mode is active. All sample values are synthetic and must not be interpreted as real conditions.")
if rain is None:
    st.error(f"Rainfall data unavailable: {rmeta.get('error', 'Source did not return usable data')}. Switch to Demo mode to explore interactions.")

end = rain.dropna().date.max() if rain is not None and rain.rain_mm.notna().any() else None
latest_total, latest_anomaly = latest_summary(rain, end, 7, BASE0, BASE1) if end is not None else (None, None)
ndvi_anomaly = cc.ndvi_anomaly(ndvi, BASE0, BASE1) if ndvi is not None and not ndvi.empty else None

# --- Pages ---
if page == "Overview":
    st.subheader("Indus Basin · Pilot overview")
    cols = st.columns(4)
    with cols[0]: card("Rainfall · latest 7 complete days", fmt_mm(latest_total),
                       f"{latest_anomaly['pct']:+.1f}% vs reference" if latest_anomaly and latest_anomaly.get("pct") is not None else "Historical comparison unavailable",
                       rmeta["source"], rmeta["cls"], f"· through {end:%d %b %Y}" if end is not None else "")
    with cols[1]: card("Official flood status", flood["status"] if flood else "No bulletin loaded",
                       "Official bulletin · not a probability", flood["source"] if flood else "PMD / FFD import", flood["cls"] if flood else "Unavailable")
    with cols[2]: card("Vegetation condition", f"{ndvi_anomaly['latest']:.2f}" if ndvi_anomaly else "Not available",
                       f"{ndvi_anomaly['pct']:+.1f}% vs same-month baseline" if ndvi_anomaly else "MODIS extraction not configured",
                       nmeta["source"], nmeta["cls"])
    with cols[3]: card("Yield outlook", "Under development", "Requires crop-specific validated model", "Not available", "Model estimate")

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown("### Pilot geography")
        rows = [{"district": d, "province": p, "selection": "Selected district" if (d == district and p == province) else "Other pilot district"}
                for p, items in DISTRICTS.items() for d in items]
        fig = px.choropleth_map(pd.DataFrame(rows), geojson=GEOJSON, locations="district",
                                featureidkey="properties.district", color="selection",
                                color_discrete_map={"Selected district": "#E05A47", "Other pilot district": "#8DBCE8"},
                                hover_name="district", hover_data={"province": True, "selection": False, "district": False},
                                center={"lat": coords[0], "lon": coords[1]}, zoom=5.1, opacity=.7, height=420)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title="")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Geographic locator only. The highlighted district is not a mapped flood-risk classification.")
    with right:
        st.markdown("### Recent rainfall")
        if rain is not None:
            recent = rain.dropna().tail(120)
            st.plotly_chart(make_rain_chart(recent, "Daily rainfall · recent 120 records"), use_container_width=True)
        else:
            st.info("Rainfall chart will appear when a source is available.")
        st.markdown("### Evidence status")
        st.write(f"- Rainfall: **{rmeta['cls']}**")
        st.write(f"- Flood: **{flood['cls'] if flood else 'No official bulletin loaded'}**")
        st.write(f"- Vegetation: **{nmeta['cls']}**")
    st.info("ResilientEarth complements official warnings. Rainfall observations, official flood bulletins, satellite-observed inundation and model probabilities are different evidence types.")

elif page == "Rainfall Explorer":
    st.subheader("Interactive rainfall explorer")
    if rain is None or rain.empty:
        st.warning("No rainfall dataset is available for this district.")
        st.stop()
    min_date, max_date = rain.date.min().date(), rain.date.max().date()
    default_start = max(min_date, max_date - dt.timedelta(days=365 * 3))
    selected = st.date_input("Analysis period", value=(default_start, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected, tuple) and len(selected) == 2:
        start_date, end_date = selected
    else:
        start_date, end_date = min_date, max_date
    period = safe_period(rain, start_date, end_date)
    aggregation = st.radio("View", ["Daily", "Monthly", "Monsoon season"], horizontal=True)
    if aggregation == "Daily":
        view = period.copy()
        fig = make_rain_chart(view, f"Daily rainfall · {start_date} to {end_date}")
    elif aggregation == "Monthly":
        view = rf.monthly(period, min_coverage=.80)
        fig = px.bar(view, x="date", y="mm", title="Monthly rainfall · months below 80% coverage are blank",
                     labels={"mm": "Rainfall (mm)", "date": "Month"})
    else:
        view = rf.seasonal_totals(period, min_coverage=.80)
        fig = px.bar(view, x="year", y="total_mm", title="Monsoon totals · incomplete seasons excluded",
                     labels={"total_mm": "June–September rainfall (mm)", "year": "Year"})
    st.plotly_chart(fig, use_container_width=True)
    if aggregation == "Monsoon season":
        trend_series = rf.seasonal_totals(rain, min_coverage=MIN_COVERAGE)
        eligible = trend_series[trend_series.complete & trend_series.total_mm.notna()]
        st.markdown("### Long-term monsoon trend screening")
        if len(eligible) >= MIN_TREND_YEARS:
            trend = rf.mann_kendall(eligible.total_mm.to_numpy(), years=eligible.year.to_numpy())
            t1, t2, t3 = st.columns(3)
            t1.metric("Mann–Kendall result", trend["trend"])
            t2.metric("Sen's slope", f"{trend['sen_slope']:+.2f} mm/year")
            t3.metric("p-value", f"{trend['p']:.4f}")
            st.caption(f"{trend['n']} complete monsoon seasons. Tie correction applied. This is trend screening, not attribution; assess serial dependence and dataset consistency before drawing climate conclusions.")
        else:
            st.info(f"Trend screening withheld: {len(eligible)} complete seasons available; at least {MIN_TREND_YEARS} are required.")
    valid = period.rain_mm.notna().sum()
    expected = len(pd.date_range(start_date, end_date, freq="D"))
    m1, m2, m3 = st.columns(3)
    m1.metric("Available daily records", f"{valid:,}")
    m2.metric("Period coverage", f"{valid / expected:.1%}" if expected else "n/a")
    m3.metric("Period accumulation", fmt_mm(period.rain_mm.sum(min_count=1)))
    st.download_button("⬇ Download selected rainfall data (CSV)", period.to_csv(index=False).encode("utf-8"),
                       file_name=f"resilientearth_{district.lower().replace(' ', '_')}_rainfall.csv", mime="text/csv")
    with st.expander("How to interpret this chart"):
        st.write("Monthly totals require at least 80% daily coverage. Monsoon totals require at least 80% coverage of the June–September season. Missing days are not treated as zero rainfall.")
        st.write(f"Source: {rmeta['source']} · Classification: {rmeta['cls']} · Method: {rmeta.get('method', 'Not specified')}.")

elif page == "District Compare":
    st.subheader("Compare districts")
    st.caption("Live comparison uses one NASA POWER point query per selected district. Bounding-box centre points are not district-wide spatial averages.")
    all_districts = [(p, d) for p, items in DISTRICTS.items() for d in items]
    labels = [f"{d} · {p}" for p, d in all_districts]
    default_labels = [f"{district} · {province}"]
    picked = st.multiselect("Choose 2–5 districts", labels, default=default_labels, max_selections=5)
    days = st.select_slider("Accumulation window", options=[1, 3, 7, 14, 30], value=7, format_func=lambda x: f"{x} days")
    if st.button("Compare selected districts", type="primary", disabled=len(picked) < 2):
        records = []
        progress = st.progress(0)
        for i, label in enumerate(picked):
            d, p = label.split(" · ")
            df, meta = ds.get_rainfall(d, DISTRICTS[p][d], demo)
            if df is not None and df.rain_mm.notna().any():
                e = df.dropna().date.max()
                total = rf.window_total(df, e, days, min_coverage=1.0)
                records.append({"District": d, "Province": p, f"Rainfall · {days}d (mm)": total,
                                "Data classification": meta["cls"], "Valid through": e.date().isoformat()})
            else:
                records.append({"District": d, "Province": p, f"Rainfall · {days}d (mm)": None,
                                "Data classification": "Unavailable", "Valid through": "—"})
            progress.progress((i + 1) / len(picked))
        st.session_state["district_comparison"] = records
    if st.session_state.get("district_comparison"):
        result = pd.DataFrame(st.session_state["district_comparison"])
        st.dataframe(result, use_container_width=True, hide_index=True)
        numeric = result.dropna(subset=[f"Rainfall · {days}d (mm)"])
        if not numeric.empty:
            st.plotly_chart(px.bar(numeric, x="District", y=f"Rainfall · {days}d (mm)", color="Province", title="Comparable latest accumulation"), use_container_width=True)
        st.caption("Comparison is descriptive, not a ranking of flood risk. Different district retrieval dates or missing records can affect comparability.")
        st.download_button("⬇ Download comparison", result.to_csv(index=False).encode(), "district_comparison.csv", "text/csv")

elif page == "Monsoon Scenario Lab":
    st.subheader("Monsoon scenario lab")
    st.warning("Scenario simulator only — not a forecast, warning, hydrological model or probability estimate.")
    if rain is None or end is None:
        st.info("Rainfall data is required to build a scenario. Enable Demo mode to explore the interaction.")
        st.stop()
    season_start = st.date_input("Choose a reference date", value=end.date(), min_value=rain.date.min().date(), max_value=end.date())
    window = st.select_slider("Scenario accumulation window", options=[3, 7, 14, 30], value=7, format_func=lambda x: f"{x} days")
    multiplier = st.slider("Hypothetical rainfall multiplier", min_value=0.5, max_value=3.0, value=1.5, step=0.1)
    base_total = rf.window_total(rain, pd.Timestamp(season_start), window, min_coverage=1.0)
    if pd.notna(base_total):
        scenario_total = base_total * multiplier
        st.markdown("### Scenario result")
        a, b, c = st.columns(3)
        a.metric("Observed reference accumulation", f"{base_total:.1f} mm")
        b.metric("Scenario accumulation", f"{scenario_total:.1f} mm", f"{(multiplier - 1) * 100:+.0f}% hypothetical change")
        c.metric("Multiplier", f"{multiplier:.1f}×")
        base = rf.baseline_totals(rain, pd.Timestamp(season_start), window, BASE0, BASE1, min_coverage=1.0)
        if len(base) >= 5:
            percentile = (base < scenario_total).mean() * 100
            st.write(f"In this historical comparison sample (n={len(base)}), the scenario amount exceeds approximately **{percentile:.0f}%** of reference-period totals.")
        else:
            st.info("Not enough complete historical comparison windows to calculate a percentile.")
        st.caption("This is a mathematical what-if transformation of the selected historical accumulation. It does not estimate river levels, inundation, damage or flood probability.")
    else:
        st.warning("The selected reference window has missing daily observations. Choose a date with complete coverage.")

elif page == "Flood Intelligence":
    st.subheader("Flood intelligence")
    st.markdown("### Official information")
    if flood:
        st.metric("Latest imported bulletin status", flood["status"])
        st.caption(f"{flood['source']} · {flood['cls']}")
    else:
        st.info("No official bulletin is currently loaded for this district. Import verified PMD/FFD bulletins using the CSV template in the repository.")
    st.markdown("### Evidence layers")
    st.write("- **Rainfall:** NASA POWER point estimate; not a river-flow forecast.")
    st.write("- **Observed inundation:** NASA LANCE VIIRS integration is planned; no flood extent is asserted here.")
    st.write("- **Official forecast:** PMD/FFD integration is via controlled bulletin import; check the issuing authority for current warnings.")
    st.write("- **Flood probability:** not displayed because a validated, event-labelled model is not yet implemented.")
    st.link_button("Pakistan Meteorological Department", "https://weather.gov.pk/")
    st.link_button("Flood Forecasting Division", "https://ffd.pmd.gov.pk/")

elif page == "Agricultural Impact":
    st.subheader("Agricultural condition")
    if ndvi is None or ndvi.empty:
        st.info("MODIS NDVI/EVI is not yet configured. Place validated district-level processed data in data/processed/ndvi_<district>.parquet.")
    else:
        st.plotly_chart(px.line(ndvi, x="date", y="ndvi", title=f"Vegetation index · {district}", range_y=[0, 1]), use_container_width=True)
        if ndvi_anomaly:
            a, b = st.columns(2)
            a.metric("Latest NDVI", f"{ndvi_anomaly['latest']:.3f}")
            b.metric("Same-month baseline difference", f"{ndvi_anomaly['pct']:+.1f}%")
    st.caption("NDVI is a vegetation-condition indicator, not a direct crop-yield or crop-loss measurement. Cloud, crop type, phenology and quality flags matter.")

elif page == "Earth Intelligence Search":
    st.subheader("Earth intelligence search")
    st.caption("Searches the web on demand using your Serper API key. Search results are leads; verify important claims against the original issuing agency.")
    topics = ["flood warning", "heavy rainfall forecast", "river flow and flood situation", "agriculture and crop conditions"]
    topic = st.selectbox("Information focus", topics)
    extra = st.text_input("Optional search refinement", placeholder="e.g. Chenab River, South Punjab, date range")
    query = f"Pakistan {province} {district} {topic} {extra}".strip()
    if st.button("Search current information", type="primary"):
        key = get_secret("SERPER_API_KEY")
        try:
            with st.spinner("Searching for relevant reports..."):
                results = serper_search(query, key, num=8)
            st.session_state["serper_results"] = results
            st.session_state["serper_query"] = query
        except Exception as exc:
            st.error(f"Search could not be completed: {type(exc).__name__}: {exc}")
    if st.session_state.get("serper_results") is not None:
        st.caption(f"Search: {st.session_state.get('serper_query', '')}")
        results = st.session_state["serper_results"]
        if not results:
            st.info("No organic results were returned.")
        for item in results:
            st.markdown(f"**[{item.get('title', 'Untitled result')}]({item.get('link', '#')})**")
            if item.get("date"):
                st.caption(item["date"])
            st.write(item.get("snippet", "No summary supplied."))
            st.divider()
    st.caption("Do not treat search snippets as official warnings or verified measurements. Follow PMD, FFD and provincial disaster-management authorities for operational decisions.")

elif page == "Data & Methodology":
    st.subheader("Data, methods and evidence")
    rows = [
        ["NASA POWER PRECTOTCORR", "Daily point query", "Rainfall context", "Gridded meteorological estimate", "Connected"],
        ["NASA GPM IMERG V07", "Half-hourly / 0.1°", "Spatial rainfall", "Satellite precipitation estimate", "Planned"],
        ["MODIS MOD13Q1.061", "16-day / 250 m", "NDVI/EVI", "Satellite observation", "Processed input required"],
        ["NASA LANCE VIIRS", "Near-real-time products", "Flood observations", "Satellite-derived event observation", "Planned"],
        ["PMD / FFD", "Bulletins and forecasts", "Official flood/weather information", "Official source product", "Controlled CSV import"],
        ["Serper Search", "On demand", "Discover reports and updates", "Web search result; not a measurement", "Optional key"],
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Source", "Temporal / spatial scale", "Use", "Evidence class", "Integration status"]), use_container_width=True, hide_index=True)
    st.markdown("### Analytical rules")
    st.write(f"- Proposed anomaly reference period: **{BASE0}–{BASE1}**. Confirm suitability separately for each dataset and indicator.")
    st.write("- Seven-day rainfall requires complete daily records for the displayed accumulation.")
    st.write("- Monthly and monsoon aggregates below 80% coverage are withheld.")
    st.write(f"- Mann–Kendall trend screening requires at least {MIN_TREND_YEARS} complete monsoon seasons at ≥{MIN_COVERAGE:.0%} coverage. Tie correction is applied; serial dependence still requires assessment.")
    st.write("- Sen's slope is reported per year when actual year labels are supplied.")
    st.write("- Missing data remain missing; they are never silently replaced with zero.")
    st.markdown("### Current district data provenance")
    st.json({"district": district, "province": province, "rainfall": rmeta,
             "vegetation": nmeta, "flood_bulletin": flood or "No bulletin available"})
    if rain is not None:
        st.download_button("⬇ Download raw rainfall series", rain.to_csv(index=False).encode(),
                           f"{district.lower().replace(' ', '_')}_rainfall_source.csv", "text/csv")

st.divider()
st.caption("ResilientEarth v0.2 · Indus Basin pilot · Evidence before prediction · Validation before probability · Transparency before claims")
