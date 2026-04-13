import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Road Accidents — Almaty", layout="wide", page_icon="🚗")

# ─── District centroids (for accident heatmap) ───────────────────────────────
DISTRICT_COORDS = {
    191910: {"lat": 43.2565, "lon": 76.9286, "name": "Алмалинский",   "name_en": "Almalinsky"},
    191960: {"lat": 43.2200, "lon": 76.8900, "name": "Бостандыкский", "name_en": "Bostandyk"},
    191956: {"lat": 43.2300, "lon": 76.9700, "name": "Медеуский",     "name_en": "Medeu"},
    191966: {"lat": 43.3100, "lon": 77.0200, "name": "Турксибский",   "name_en": "Turksib"},
    191932: {"lat": 43.2900, "lon": 76.9900, "name": "Жетысуский",    "name_en": "Zhetysu"},
    191934: {"lat": 43.1700, "lon": 76.8100, "name": "Наурызбайский", "name_en": "Nauryzbay"},
    191916: {"lat": 43.2100, "lon": 76.8300, "name": "Ауэзовский",    "name_en": "Auezov"},
    191926: {"lat": 43.3400, "lon": 76.8800, "name": "Алатауский",    "name_en": "Alatau"},
    191940: {"lat": 43.2700, "lon": 76.9100, "name": "Жетысуский 2",  "name_en": "Zhetysu-2"},
    191964: {"lat": 43.2400, "lon": 76.8500, "name": "Наурызбай 2",   "name_en": "Nauryzbay-2"},
}

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_accidents():
    df = pd.read_csv("datasets/processed_table.csv", parse_dates=["Accident_Date"])
    df["Severe_Accident"] = (df["Number_of_Injured"] > 1).astype(int)
    df["Year"]  = df["Accident_Date"].dt.year
    df["Month"] = df["Accident_Date"].dt.month
    return df

@st.cache_resource
def train_model(df):
    from sklearn.ensemble import RandomForestClassifier
    cat_cols = ["Accident_Location", "District"]
    X = df.drop(columns=["Accident_Type", "Accident_Date", "Number_of_Injured", "Severe_Accident"])
    X = pd.get_dummies(X, columns=cat_cols)
    y = df["Severe_Accident"]
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42,
                                 class_weight="balanced", n_jobs=-1)
    rf.fit(X, y)
    return rf, X.columns

try:
    df = load_accidents()
    data_ok = True
except FileNotFoundError:
    st.error("⚠️ Could not find `datasets/processed_table.csv`. Place the dataset next to the app.")
    st.stop()

# ─── Train model (cached) ─────────────────────────────────────────────────────
with st.spinner("Training Random Forest model... (first run only)"):
    model, model_cols = train_model(df)

# ─── Page header ──────────────────────────────────────────────────────────────
st.title("🚗 Road Accidents — Almaty")
st.markdown("Accident hotspot maps, statistics, and ML-powered severity prediction.")

tab1, tab2 = st.tabs(["📊 Dashboard & Map", "🤖 Severity Predictor"])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — Dashboard
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    # ── Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        year_range = st.slider("Year range",
                               int(df["Year"].min()), int(df["Year"].max()),
                               (int(df["Year"].min()), int(df["Year"].max())))
        weather_opts = sorted(df["Weather_Conditions"].dropna().unique())
        sel_weather  = st.multiselect("Weather", weather_opts, default=weather_opts[:3])

    fdf = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    if sel_weather:
        fdf = fdf[fdf["Weather_Conditions"].isin(sel_weather)]

    # ── KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accidents", f"{len(fdf):,}")
    c2.metric("Severe Accidents", f"{fdf['Severe_Accident'].sum():,}")
    c3.metric("Severity Rate", f"{fdf['Severe_Accident'].mean()*100:.1f}%")
    c4.metric("Avg Injured / Accident", f"{fdf['Number_of_Injured'].mean():.2f}")

    st.markdown("---")

    # ── Map
    st.subheader("🗺️ Accident Heatmap by District")
    dist_counts = fdf.groupby("District").agg(
        total=("Severe_Accident", "count"),
        severe=("Severe_Accident", "sum")
    ).reset_index()

    map_rows = []
    for _, row in dist_counts.iterrows():
        d = int(row["District"])
        if d in DISTRICT_COORDS:
            coords = DISTRICT_COORDS[d]
            severity_rate = row["severe"] / row["total"] if row["total"] > 0 else 0
            r = int(255 * severity_rate)
            g = int(255 * (1 - severity_rate))
            map_rows.append({
                "lat": coords["lat"], "lon": coords["lon"],
                "name_en": coords["name_en"],
                "total": int(row["total"]),
                "severe": int(row["severe"]),
                "severity_pct": f"{severity_rate*100:.1f}%",
                "color": [r, g, 50, 180],
                "radius": max(800, int(row["total"] * 15)),
            })

    if map_rows:
        map_df = pd.DataFrame(map_rows)
        layer = pdk.Layer("ScatterplotLayer", data=map_df,
                           get_position=["lon", "lat"], get_color="color",
                           get_radius="radius", opacity=0.75, pickable=True)
        text_layer = pdk.Layer("TextLayer", data=map_df,
                                get_position=["lon", "lat"], get_text="name_en",
                                get_size=14, get_color=[255,255,255])
        view = pdk.ViewState(latitude=43.25, longitude=76.93, zoom=10, pitch=35)
        tooltip = {
            "html": "<b>{name_en}</b><br/>Total: <b>{total}</b><br/>Severe: <b>{severe}</b><br/>Severity rate: {severity_pct}",
            "style": {"background": "#1e1e2e", "color": "white", "borderRadius": "8px", "padding": "8px"}
        }
        st.pydeck_chart(pdk.Deck(layers=[layer, text_layer], initial_view_state=view,
                                  tooltip=tooltip, map_style="mapbox://styles/mapbox/dark-v10"))
        st.markdown("🟢 Low severity &nbsp;&nbsp; 🟡 Medium &nbsp;&nbsp; 🔴 High severity rate")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Accidents by Location Type")
        loc_c = fdf["Accident_Location"].value_counts().head(10)
        fig = px.bar(loc_c, orientation="h", color=loc_c.values,
                     color_continuous_scale="Reds", labels={"value":"Count","index":"Location"})
        fig.update_layout(template="plotly_dark", showlegend=False, yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Severity by Weather")
        wdf = fdf.groupby("Weather_Conditions")["Severe_Accident"].mean().sort_values(ascending=False)
        fig2 = px.bar(wdf, color=wdf.values, color_continuous_scale="RdYlGn_r",
                      labels={"value":"Severity Rate","index":"Weather"})
        fig2.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📅 Monthly Accident Trend")
    monthly = fdf.groupby(["Year","Month"]).size().reset_index(name="count")
    monthly["date"] = pd.to_datetime(monthly[["Year","Month"]].assign(day=1))
    fig3 = px.line(monthly, x="date", y="count", title="Monthly Accidents")
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Predictor
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("🤖 Predict Accident Severity")
    st.markdown("Enter accident conditions below to get a ML-based severity prediction.")

    c1, c2 = st.columns(2)
    with c1:
        accident_location = st.selectbox("Accident Location", sorted(df["Accident_Location"].dropna().unique()))
        district          = st.selectbox("District", sorted(df["District"].dropna().unique()))
        weather           = st.selectbox("Weather Conditions", sorted(df["Weather_Conditions"].dropna().unique()))
        speed_limit       = st.slider("Speed Limit (km/h)", 20, 140, 60, step=10)
    with c2:
        lighting          = st.selectbox("Lighting Conditions", sorted(df["Lighting_Conditions"].dropna().unique()))
        street_lighting   = st.selectbox("Street Lighting at Night", sorted(df["Street_Lighting_Night"].dropna().unique()))
        road_surface      = st.selectbox("Road Surface", sorted(df["Road_Surface_Condition"].dropna().unique()))
        gender            = st.selectbox("Fault Person Gender", sorted(df["Fault_Person_Gender"].dropna().unique()))

    if st.button("🔮 Predict Severity", type="primary"):
        input_data = {
            "Lighting_Conditions": [lighting], "Street_Lighting_Night": [street_lighting],
            "Weather_Conditions": [weather], "Speed_Limit": [speed_limit],
            "Fault_Person_Gender": [gender], "Road_Surface_Condition": [road_surface],
            "Accident_Location": [accident_location], "District": [district],
            "Fault_Person_Condition": [0],
        }
        input_df = pd.DataFrame(input_data)
        input_df = pd.get_dummies(input_df, columns=["Accident_Location", "District"])
        input_df = input_df.reindex(columns=model_cols, fill_value=0)

        pred  = model.predict(input_df)[0]
        proba = model.predict_proba(input_df)[0][1]

        st.markdown("---")
        if pred == 1:
            st.error(f"### ⚠️ Severe Accident Likely\nProbability: **{proba:.1%}**")
        else:
            st.success(f"### ✅ Accident Likely NOT Severe\nProbability of severity: **{proba:.1%}**")

        # Gauge chart
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=proba * 100,
            title={"text": "Severity Probability (%)"},
            gauge={"axis": {"range": [0, 100]},
                   "bar": {"color": "#e94560"},
                   "steps": [
                       {"range": [0, 30],  "color": "#1a2e1a"},
                       {"range": [30, 60], "color": "#2e2a1a"},
                       {"range": [60, 100],"color": "#2e1a1a"},
                   ]}
        ))
        fig_g.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_g, use_container_width=True)
