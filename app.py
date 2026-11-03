import pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit as st
from config.settings import *
from services import data_service as ds
from analytics import rainfall as rf, crop_condition as cc
from components.ui import inject_css, card, badge

st.set_page_config(page_title="ResilientEarth", page_icon="🌍", layout="wide")
inject_css()
with st.sidebar:
    st.markdown("## 🌍 ResilientEarth"); st.caption("Explore • Understand • Prepare")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    prov = st.selectbox("Province", list(DISTRICTS))
    dist = st.selectbox("District", list(DISTRICTS[prov]))
    demo = st.toggle("Demo Mode (sample data)", False)
    if st.button("🔄 Refresh data"):
        st.cache_data.clear(); st.rerun()

coords = DISTRICTS[prov][dist]
rain, rmeta = ds.get_rainfall(dist, coords, demo)
ndvi, nmeta = ds.get_ndvi(dist, demo)
flood = ds.get_flood(dist, demo)

st.title("ResilientEarth")
st.caption(f"Earth System Intelligence for a Resilient Future · {dist}, {prov} · Retrieved: {rmeta.get('retrieved', 'n/a')}")
if demo:
    st.warning("DEMO MODE: sample data, not live observations.")
if rain is None:
    st.error(f"Rainfall source unavailable ({rmeta.get('error')}). No values are shown. Try Refresh or Demo Mode.")

end = rain.dropna().date.max() if rain is not None else None
tot = rf.window_total(rain, end, 7) if rain is not None else None
an = rf.anomaly(tot, rf.baseline_totals(rain, end, 7, BASE0, BASE1)) if rain is not None else None
na = cc.ndvi_anomaly(ndvi, BASE0, BASE1) if ndvi is not None else None

def rain_card():
    if an is None: return card("Rainfall (7d)", "Data unavailable", "", rmeta["source"], rmeta["cls"])
    card("Rainfall (7d)", f"{tot:.0f} mm", f"{an['pct']:+.0f}% vs {BASE0}-{BASE1} mean · percentile {an['percentile']:.0f}",
         rmeta["source"], rmeta["cls"], f"· to {end:%Y-%m-%d}")
def flood_card():
    if flood is None: return card("Flood Status", "Data unavailable", "No official bulletin imported", "FFD/PMD", "Official bulletin (imported)")
    card("Flood Status", flood["status"], "Official status; not a probability", flood["source"], flood["cls"])
def ndvi_card():
    if na is None: return card("Crop Health (NDVI)", "Data unavailable", "Run MODIS extraction", nmeta["source"], nmeta["cls"])
    card("Crop Health (NDVI)", f"{na['latest']:.2f}", f"{na['pct']:+.0f}% vs baseline", nmeta["source"], nmeta["cls"], f"· {na['date']:%Y-%m-%d}")
def yield_card():
    card("Yield Outlook", "Under development", "Needs validated yield model", "n/a", "Model estimate")

def key_insights():
    st.subheader("Key insights")
    out = []
    if an: out.append(f"Rainfall in {dist} over the last 7 days is {an['pct']:+.0f}% relative to the {BASE0}-{BASE1} mean (percentile {an['percentile']:.0f}).")
    if na: out.append(f"Latest NDVI is {na['latest']:.2f}, {na['pct']:+.0f}% relative to the same-month baseline.")
    if flood: out.append(f"Flood status: {flood['status']} ({flood['source']}).")
    for t in out: st.markdown(f"✅ {t}")
    if not out: st.info("No insights: required data unavailable.")
    st.caption("Follow official warnings from PMD, FFD and disaster authorities.")

def map_fig():
    rows = [dict(district=d, lat=c[0], lon=c[1], sel=("Selected" if d == dist else "Pilot district")) for p in DISTRICTS.values() for d, c in p.items()]
    f = px.scatter_map(pd.DataFrame(rows), lat="lat", lon="lon", hover_name="district", color="sel", size=[16 if r["sel"] == "Selected" else 9 for r in rows],
                       color_discrete_map={"Selected": "#E74C3C", "Pilot district": "#1E88E5"}, zoom=4.6, height=380)
    f.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title=""); return f

def seasonal_chart():
    s = rf.seasonal_totals(rain)
    clim = s[s.year.between(BASE0, BASE1)].total_mm.mean()
    f = px.bar(s, x="year", y="total_mm", labels={"total_mm": "Jun-Sep rainfall (mm)"}, color_discrete_sequence=["#1E88E5"])
    f.add_hline(y=clim, line_dash="dash", annotation_text=f"{BASE0}-{BASE1} mean"); return f, s

if page == "Overview":
    c = st.columns(4)
    for col, fn in zip(c, [rain_card, flood_card, ndvi_card, yield_card]):
        with col: fn()
    a, b = st.columns([3, 2])
    with a:
        st.subheader("Pilot districts map"); st.plotly_chart(map_fig(), use_container_width=True)
        st.caption("Centroids only. Add district boundary GeoJSON and rainfall/flood layers (Phase 2-4).")
    with b:
        st.subheader(f"Rainfall trends: {dist}")
        if rain is not None: st.plotly_chart(seasonal_chart()[0], use_container_width=True)
    key_insights()

elif page == "Rainfall Trends":
    st.subheader(f"Rainfall trends: {dist}")
    if rain is None: st.stop()
    f, s = seasonal_chart(); st.plotly_chart(f, use_container_width=True)
    ok = s[s.coverage >= MIN_COVERAGE]
    if len(ok) < MIN_TREND_YEARS: st.info(f"Insufficient data for trend analysis: {len(ok)} years with >= {MIN_COVERAGE:.0%} coverage.")
    else:
        r = rf.mann_kendall(ok.total_mm)
        st.markdown(f"**Mann-Kendall** ({ok.year.min()}-{ok.year.max()}, n={r['n']}): {r['trend']} (p={r['p']:.3f}); **Sen's slope** {r['sen_slope']:+.1f} mm/yr. Monsoon (Jun-Sep) totals; no tie correction.")
    m = rf.monthly(rain); m["month"] = m.date.dt.month
    clim = m[m.date.dt.year.between(BASE0, BASE1)].groupby("month").mm.mean().reset_index()
    st.plotly_chart(px.line(clim, x="month", y="mm", title=f"Monthly climatology {BASE0}-{BASE1}"), use_container_width=True)

elif page == "Flood Intelligence":
    st.subheader("Flood intelligence")
    st.markdown("Official status, observed inundation (NASA LANCE VIIRS), forecasts and model estimates are kept separate.")
    if flood: st.metric("Official status", flood["status"]); st.caption(f"{flood['source']} · {flood['cls']}")
    else: st.info("Data unavailable. Add bulletins to data/reference/official_bulletins.csv (see README).")
    st.info("Observed flood extent (NASA LANCE): under development. Flood probability: not displayed until validated.")
    if flood and "exposed_ha" in flood: st.metric("Potentially exposed cropland (sample)", f"{flood['exposed_ha']:,} ha")

elif page == "Agricultural Impact":
    st.subheader("Agricultural impact")
    if na is None: st.info("Data unavailable. Run the MODIS extraction (data_connectors/nasa_modis.py).")
    else:
        st.plotly_chart(px.line(ndvi, x="date", y="ndvi", title="NDVI"), use_container_width=True)
        st.metric("NDVI anomaly", f"{na['pct']:+.1f}%")
    st.caption("NDVI is not a yield measure. Exposed cropland is not confirmed damage. Yield Outlook: under development.")

elif page == "District Investigation":
    st.subheader(f"{dist}, {prov}")
    c = st.columns(4)
    for col, fn in zip(c, [rain_card, flood_card, ndvi_card, yield_card]):
        with col: fn()
    if rain is not None:
        st.write(f"Rainfall record: {rain.date.min():%Y-%m-%d} to {end:%Y-%m-%d}; coverage {rain.rain_mm.notna().mean():.1%}.")

else:
    st.subheader("Data & Methodology")
    st.table(pd.DataFrame([
        ["NASA POWER PRECTOTCORR", "Daily, ~0.5 deg", "Rainfall (live, coarse)", "Observation/reanalysis blend", "Live"],
        ["NASA GPM IMERG V07", "Daily, 0.1 deg", "Rainfall", "Observation", "Planned (Phase 2)"],
        ["MODIS MOD13Q1.061", "16-day, 250 m", "NDVI/EVI", "Observation", "Planned (offline extraction)"],
        ["NASA LANCE VIIRS", "Event", "Flood extent", "Observation", "Planned (Phase 4)"],
        ["PMD / FFD", "Bulletins", "Official status", "Official (imported)", "CSV import"],
    ], columns=["Dataset", "Resolution", "Use", "Class", "Status"]))
    st.markdown(f"Anomaly baseline {BASE0}-{BASE1}. Trends: Mann-Kendall, Sen's slope, alpha 0.05, min {MIN_TREND_YEARS} years, {MIN_COVERAGE:.0%} coverage. Missing values stay missing.")
