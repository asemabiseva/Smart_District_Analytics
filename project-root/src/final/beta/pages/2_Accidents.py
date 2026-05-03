import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
ACCIDENTS_DATASET = SCRIPT_DIR / "datasets/jestka_preprocessed_dataset.csv"

from app import (
    apply_base_style,
    render_theme_toggle,
    max_dataset_mtime,
    render_data_freshness,
    render_feedback_widget,
    render_glossary,
    render_insight,
    render_page_intro,
    severity_bucket,
    sidebar_common_filters,
    RISK_COLORS,
)

st.set_page_config(page_title="Road Accidents - Almaty", layout="wide", page_icon="🚗")
apply_base_style()
render_theme_toggle()

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

MODEL_CAT_COLS = [
    "Accident_Location",
    "District",
    "Weather_Conditions",
    "Lighting_Conditions",
    "Street_Lighting_Night",
    "Road_Surface_Condition",
    "Fault_Person_Gender",
    "Fault_Person_Condition",
]

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_accidents():
    df = pd.read_csv(str(ACCIDENTS_DATASET), parse_dates=["Accident_Date"])

    # Backward-compatible normalization so downstream visuals/predictor keep working.
    if "Accident_District" in df.columns and "District" not in df.columns:
        df["District"] = df["Accident_District"]

    weather_cols = [c for c in df.columns if c.startswith("weather_")]
    if "Weather_Conditions" not in df.columns and weather_cols:
        weather_names = {c: c.replace("weather_", "") for c in weather_cols}
        best = df[weather_cols].astype(float).idxmax(axis=1)
        no_signal = df[weather_cols].astype(float).sum(axis=1) == 0
        df["Weather_Conditions"] = best.map(weather_names)
        df.loc[no_signal, "Weather_Conditions"] = "unknown"

    if "Lighting_Conditions" not in df.columns:
        if {"is_day", "is_night", "is_twilight"}.issubset(df.columns):
            df["Lighting_Conditions"] = np.select(
                [df["is_day"] == 1, df["is_twilight"] == 1, df["is_night"] == 1],
                ["day", "twilight", "night"],
                default="unknown",
            )
        else:
            df["Lighting_Conditions"] = "unknown"

    if "Street_Lighting_Night" not in df.columns:
        if "night_without_lighting" in df.columns:
            df["Street_Lighting_Night"] = (df["night_without_lighting"] == 0).astype(int)
        else:
            df["Street_Lighting_Night"] = 0

    road_cols = [c for c in df.columns if c.startswith("road_")]
    if "Road_Surface_Condition" not in df.columns and road_cols:
        road_names = {c: c.replace("road_", "") for c in road_cols}
        best = df[road_cols].astype(float).idxmax(axis=1)
        no_signal = df[road_cols].astype(float).sum(axis=1) == 0
        df["Road_Surface_Condition"] = best.map(road_names)
        df.loc[no_signal, "Road_Surface_Condition"] = "unknown"

    if "Fault_Person_Gender" not in df.columns:
        gender_cols = [c for c in df.columns if c.startswith("At_Fault_Gender_")]
        if gender_cols:
            gender_names = {c: c.replace("At_Fault_Gender_", "") for c in gender_cols}
            best = df[gender_cols].astype(float).idxmax(axis=1)
            no_signal = df[gender_cols].astype(float).sum(axis=1) == 0
            df["Fault_Person_Gender"] = best.map(gender_names)
            df.loc[no_signal, "Fault_Person_Gender"] = "unknown"
        else:
            df["Fault_Person_Gender"] = "unknown"

    if "Fault_Person_Condition" not in df.columns:
        cond_cols = [c for c in df.columns if c.startswith("Faulty_Condition_")]
        if cond_cols:
            cond_names = {c: c.replace("Faulty_Condition_", "") for c in cond_cols}
            best = df[cond_cols].astype(float).idxmax(axis=1)
            no_signal = df[cond_cols].astype(float).sum(axis=1) == 0
            df["Fault_Person_Condition"] = best.map(cond_names)
            df.loc[no_signal, "Fault_Person_Condition"] = "unknown"
        else:
            df["Fault_Person_Condition"] = "unknown"

    if "Speed_Limit" not in df.columns and "Speed_Limit_clean" in df.columns:
        df["Speed_Limit"] = df["Speed_Limit_clean"]

    df["Severe_Accident"] = (df["Number_of_Injured"] > 1).astype(int)
    df["Year"]  = df["Accident_Date"].dt.year
    df["Month"] = df["Accident_Date"].dt.month
    return df

@st.cache_resource
def train_model(df):
    from sklearn.ensemble import RandomForestClassifier
    X = df.drop(columns=["Accident_Type", "Accident_Date", "Number_of_Injured", "Severe_Accident", "Accident_Record_ID", "Card_Number"], errors="ignore")
    existing_cat_cols = [c for c in MODEL_CAT_COLS if c in X.columns]
    if existing_cat_cols:
        X = pd.get_dummies(X, columns=existing_cat_cols)
    y = df["Severe_Accident"]
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42,
                                 class_weight="balanced", n_jobs=-1)
    rf.fit(X, y)
    return rf, X.columns

try:
    df = load_accidents()
    data_ok = True
except FileNotFoundError:
    st.error("⚠️ Could not find `datasets/jestka_preprocessed_dataset.csv`. Place the dataset next to the app.")
    st.stop()

# ─── Train model (cached) ─────────────────────────────────────────────────────
with st.spinner("Training Random Forest model... (first run only)"):
    model, model_cols = train_model(df)

# ─── Page header ──────────────────────────────────────────────────────────────
st.title("Road Accidents")
render_page_intro(
    problem="Find severe crash patterns and target prevention by district and conditions.",
    how_to_use=[
        "Select year and weather filters.",
        "Read high-risk districts from the map and metrics.",
        "Use predictor tab for scenario planning and prevention.",
    ],
)
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

    selected_common_districts, _ = sidebar_common_filters(
        [v["name"] for v in DISTRICT_COORDS.values()], key_prefix="accidents"
    )

    fdf = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    if sel_weather:
        fdf = fdf[fdf["Weather_Conditions"].isin(sel_weather)]
    selected_codes = [
        code for code, meta in DISTRICT_COORDS.items() if meta["name"] in selected_common_districts
    ]
    if selected_codes:
        fdf = fdf[fdf["District"].isin(selected_codes)]

    # ── KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accidents", f"{len(fdf):,}")
    c2.metric("Severe Accidents", f"{fdf['Severe_Accident'].sum():,}")
    c3.metric("Severity Rate", f"{fdf['Severe_Accident'].mean()*100:.1f}%")
    c4.metric("Avg Injured / Accident", f"{fdf['Number_of_Injured'].mean():.2f}")

    if len(fdf):
        by_district = (
            fdf.groupby("District")["Severe_Accident"].mean().sort_values(ascending=False)
        )
        top_code = int(by_district.index[0])
        top_name = DISTRICT_COORDS.get(top_code, {}).get("name", str(top_code))
        top_rate = float(by_district.iloc[0])
        risk = severity_bucket(top_rate, 0.2, 0.35)
        render_insight(
            title="Severity hotspot",
            finding=f"{top_name} has the highest severe accident rate at {top_rate:.1%}.",
            action="Prioritize speed calming, junction redesign, and night visibility upgrades in this district.",
            risk=risk,
        )

    st.markdown("---")

    # ── Map
    st.subheader("Accident Heatmap by District")
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
            # Bucket severity into low/medium/high for clearer legend
            bucket = severity_bucket(severity_rate, 0.2, 0.35)
            hexc = RISK_COLORS.get(bucket, "#808080")
            # hex to rgba
            def hex_to_rgba(h, a=180):
                h = h.lstrip("#")
                return [int(h[i:i+2], 16) for i in (0, 2, 4)] + [a]

            color_rgba = hex_to_rgba(hexc)
            map_rows.append({
                "lat": coords["lat"], "lon": coords["lon"],
                "name_en": coords["name_en"],
                "total": int(row["total"]),
                "severe": int(row["severe"]),
                "severity_pct": f"{severity_rate*100:.1f}%",
                "color": color_rgba,
                "radius": max(800, int(row["total"] * 15)),
                "bucket": bucket,
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
        theme_mode = st.session_state.get("theme_mode", "light")
        map_style = "dark" if theme_mode == "dark" else "light"
        st.pydeck_chart(pdk.Deck(layers=[layer, text_layer], initial_view_state=view,
                                  tooltip=tooltip, map_style=map_style))
        # Legend (visual)
        st.markdown(
            f"<div style='display:flex; gap:12px; align-items:center;'>"
            f"<div style='width:14px;height:14px;background:{RISK_COLORS['low']};border-radius:3px;'></div> Low &nbsp;"
            f"<div style='width:14px;height:14px;background:{RISK_COLORS['medium']};border-radius:3px;'></div> Medium &nbsp;"
            f"<div style='width:14px;height:14px;background:{RISK_COLORS['high']};border-radius:3px;'></div> High"
            f"</div>", unsafe_allow_html=True)

        st.caption("Map uses district centroids; color indicates bucketed severity rate (Low/Medium/High). Click a district for counts.")

        # Top-5 severity bar chart for quick comprehension
        severity_by_name = (
            map_df.sort_values("severity_pct", key=lambda s: s.str.rstrip('%').astype(float), ascending=False)
            [["name_en", "severity_pct"]]
        )
        # convert percent strings to numeric
        severity_by_name["severity_num"] = severity_by_name["severity_pct"].str.rstrip('%').astype(float)
        top5 = severity_by_name.head(5).copy()
        fig_top5 = px.bar(top5, x="name_en", y="severity_num", labels={"name_en":"District","severity_num":"Severity %"},
                          title="Top 5 Districts by Severe Accident Rate", color="severity_num", color_continuous_scale=[RISK_COLORS['high'], RISK_COLORS['medium'], RISK_COLORS['low']])
        fig_top5.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_top5, use_container_width=True)

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

    st.subheader("Monthly Accident Trend")
    monthly = fdf.groupby(["Year","Month"]).size().reset_index(name="count")
    monthly["date"] = pd.to_datetime(monthly[["Year","Month"]].assign(day=1))
    fig3 = px.line(monthly, x="date", y="count", title="Monthly Accidents")
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Predictor
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Predict Accident Severity")
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
        input_df = pd.get_dummies(input_df, columns=[c for c in MODEL_CAT_COLS if c in input_df.columns])
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

render_glossary(
    {
        "Severity Rate": "Share of accidents classified as severe.",
        "Predictor probability": "Model estimate under selected conditions, not certainty.",
    }
)

render_data_freshness(
    updated_at=max_dataset_mtime(["datasets/jestka_preprocessed_dataset.csv"]),
    source_list=["jestka_preprocessed_dataset.csv"],
    limitations=[
        "District boundaries are represented by centroids for map readability.",
        "Severe accident target is derived from injury count threshold.",
    ],
)

render_feedback_widget("Accidents")
