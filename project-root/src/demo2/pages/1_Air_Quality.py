import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Air Quality — Almaty", layout="wide", page_icon="🌬️")

# ─── Almaty district centroids ───────────────────────────────────────────────
DISTRICT_COORDS = {
    "Алмалинский":   {"lat": 43.2565, "lon": 76.9286, "name_en": "Almalinsky"},
    "Бостандыкский": {"lat": 43.2200, "lon": 76.8900, "name_en": "Bostandyk"},
    "Медеуский":     {"lat": 43.2300, "lon": 76.9700, "name_en": "Medeu"},
    "Турксибский":   {"lat": 43.3100, "lon": 77.0200, "name_en": "Turksib"},
    "Жетысуский":    {"lat": 43.2900, "lon": 76.9900, "name_en": "Zhetysu"},
    "Наурызбайский": {"lat": 43.1700, "lon": 76.8100, "name_en": "Nauryzbay"},
    "Ауэзовский":    {"lat": 43.2100, "lon": 76.8300, "name_en": "Auezov"},
    "Алатауский":    {"lat": 43.3400, "lon": 76.8800, "name_en": "Alatau"},
}

# ─── AQI color helper ─────────────────────────────────────────────────────────
def pm25_to_aqi_label(pm25):
    if pm25 <= 12:   return "Good", [0, 200, 100]
    if pm25 <= 35.4: return "Moderate", [255, 230, 0]
    if pm25 <= 55.4: return "Unhealthy for Sensitive", [255, 140, 0]
    if pm25 <= 150:  return "Unhealthy", [220, 50, 50]
    return "Very Unhealthy", [153, 0, 76]

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_air():
    df = pd.read_csv("datasets/processed_air_ala_data.csv", parse_dates=["date"])
    return df

try:
    df = load_air()
    data_ok = True
except FileNotFoundError:
    st.error("⚠️ Could not find `datasets/processed_air_ala_data.csv`. Place the dataset next to the app.")
    data_ok = False
    st.stop()

# ─── Page header ──────────────────────────────────────────────────────────────
st.title("🌬️ Air Quality — Almaty Districts")
st.markdown("Real-time PM2.5 and PM10 monitoring across 8 Almaty districts.")

# ─── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")
    date_min = df["date"].min().date()
    date_max = df["date"].max().date()
    sel_date = st.date_input("Select date", value=date_max, min_value=date_min, max_value=date_max)
    sel_districts = st.multiselect(
        "Districts", options=sorted(df["district"].unique()),
        default=list(df["district"].unique())
    )
    metric = st.radio("Pollutant", ["pm25_avg", "pm10_avg"], format_func=lambda x: x.replace("_avg","").upper())

# ─── Filter ───────────────────────────────────────────────────────────────────
day_df = df[df["date"].dt.date == sel_date]
if sel_districts:
    day_df = day_df[day_df["district"].isin(sel_districts)]

latest = day_df.groupby("district")[[metric]].mean().reset_index()
latest.columns = ["district", "value"]

# ─── KPI row ──────────────────────────────────────────────────────────────────
if len(latest):
    worst = latest.loc[latest["value"].idxmax()]
    best  = latest.loc[latest["value"].idxmin()]
    avg   = latest["value"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("🌫️ City Average " + metric.upper().replace("_AVG",""), f"{avg:.1f} µg/m³")
    c2.metric("⚠️ Worst District", worst["district"], f"{worst['value']:.1f} µg/m³")
    c3.metric("✅ Best District",  best["district"],  f"{best['value']:.1f} µg/m³")

st.markdown("---")

# ─── Map ──────────────────────────────────────────────────────────────────────
st.subheader("🗺️ District Air Quality Map")

map_data = []
for _, row in latest.iterrows():
    d = row["district"]
    if d in DISTRICT_COORDS:
        label, color = pm25_to_aqi_label(row["value"])
        coords = DISTRICT_COORDS[d]
        map_data.append({
            "district": d,
            "name_en": coords["name_en"],
            "lat": coords["lat"],
            "lon": coords["lon"],
            "value": round(row["value"], 1),
            "label": label,
            "color": color,
            "radius": max(1500, int(row["value"] * 80)),
        })

map_df = pd.DataFrame(map_data)

if len(map_df):
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radius",
        opacity=0.7,
        pickable=True,
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=map_df,
        get_position=["lon", "lat"],
        get_text="name_en",
        get_size=14,
        get_color=[255, 255, 255],
        get_alignment_baseline="'bottom'",
    )
    view = pdk.ViewState(latitude=43.25, longitude=76.93, zoom=10, pitch=30)
    tooltip = {
        "html": "<b>{district}</b><br/>PM: <b>{value} µg/m³</b><br/>Status: {label}",
        "style": {"background": "#1e1e2e", "color": "white", "borderRadius": "8px", "padding": "8px"}
    }
    st.pydeck_chart(pdk.Deck(layers=[layer, text_layer], initial_view_state=view, tooltip=tooltip,
                              map_style="mapbox://styles/mapbox/dark-v10"))

    # Legend
    st.markdown("""
    **AQI Legend:**  
    🟢 Good (≤12) &nbsp; 🟡 Moderate (12-35) &nbsp; 🟠 Unhealthy for Sensitive (35-55) &nbsp; 🔴 Unhealthy (55-150)
    """)

st.markdown("---")

# ─── Bar chart ────────────────────────────────────────────────────────────────
st.subheader("📊 Pollution by District")
if len(latest):
    fig = px.bar(
        latest.sort_values("value", ascending=False),
        x="district", y="value",
        color="value",
        color_continuous_scale=["#00C87A", "#FFE600", "#FF8C00", "#DC3232"],
        labels={"value": f"{metric.upper()} (µg/m³)", "district": "District"},
        title=f"{metric.upper()} on {sel_date}"
    )
    fig.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ─── Time series ──────────────────────────────────────────────────────────────
st.subheader("📈 Time Series by District")
ts_df = df[df["district"].isin(sel_districts)].groupby(["date", "district"])[metric].mean().reset_index()
fig2 = px.line(ts_df, x="date", y=metric, color="district",
               labels={"date": "Date", metric: f"{metric.upper()} (µg/m³)"},
               title="Daily Average Pollution Trend")
fig2.update_layout(template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)
