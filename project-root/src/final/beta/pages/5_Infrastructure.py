import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent.parent.absolute()

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
)

st.set_page_config(page_title="Infrastructure - Almaty", layout="wide", page_icon="🏫")
apply_base_style()
render_theme_toggle()

# ─── District centroids ───────────────────────────────────────────────────────
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

# Normalize district name typo in data
def normalize_district(d):
    if not isinstance(d, str):
        return d
    return d.replace("Наурызбайскйи", "Наурызбайский")

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_education():
    df = pd.read_csv(str(SCRIPT_DIR / "datasets/Almaty_Education_Master.csv"))
    df["District"] = df["District"].apply(normalize_district)
    df[["lon", "lat"]] = df["Coordinates"].str.split(",", expand=True).astype(float)
    return df

@st.cache_data
def load_hospitals():
    df = pd.read_csv(str(SCRIPT_DIR / "datasets/hospitals_almaty.csv"))
    df[["lon", "lat"]] = df["Coordinates"].str.split(",", expand=True).astype(float)
    # Assign district by nearest centroid
    def nearest_district(row):
        best, best_dist = "Unknown", 9999
        for name, c in DISTRICT_COORDS.items():
            dist = ((row["lat"] - c["lat"])**2 + (row["lon"] - c["lon"])**2)**0.5
            if dist < best_dist:
                best_dist = dist
                best = name
        return best
    df["District"] = df.apply(nearest_district, axis=1)
    return df

try:
    edu_df  = load_education()
    hosp_df = load_hospitals()
except FileNotFoundError as e:
    st.error(f"⚠️ Missing dataset: {e}")
    st.stop()

kindergartens = edu_df[edu_df["Type"] == "садик"].copy()
schools       = edu_df[edu_df["Type"] == "школа"].copy()

# ─── Page header ─────────────────────────────────────────────────────────────
st.title("Infrastructure")
render_page_intro(
    problem="Identify service gaps and districts that need education or healthcare expansion.",
    how_to_use=[
        "Choose facility layers and districts.",
        "Compare district counts and score.",
        "Use recommended actions to prioritize investments.",
    ],
)
st.markdown("Explore kindergartens, schools, and hospitals across Almaty districts.")

# ─── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("🏥 Hospitals", len(hosp_df))
c2.metric("🎒 Schools", len(schools))
c3.metric("🧒 Kindergartens", len(kindergartens))
c4.metric("🏘️ Districts Covered", edu_df["District"].nunique())

st.markdown("---")

# ─── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")
    show_kindergartens = st.checkbox("Show Kindergartens 🧒", value=True)
    show_schools       = st.checkbox("Show Schools 🎒", value=True)
    show_hospitals     = st.checkbox("Show Hospitals 🏥", value=True)
    all_districts = sorted(DISTRICT_COORDS.keys())
    sel_districts = st.multiselect("Districts", all_districts, default=all_districts)

common_districts, _ = sidebar_common_filters(all_districts, key_prefix="infra")
if common_districts:
    sel_districts = [d for d in sel_districts if d in common_districts]

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗺️ Interactive Map", "📊 District Comparison", "🏆 Livability Score"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Interactive Map
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("🗺️ Infrastructure Map")
    st.markdown("Each dot is an actual location from the dataset. Toggle layers in the sidebar.")

    layers = []

    if show_kindergartens:
        k_filt = kindergartens[kindergartens["District"].isin(sel_districts)].copy()
        k_filt["color"] = [[255, 165, 0, 200]] * len(k_filt)   # orange
        k_filt["radius"] = 80
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=k_filt,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            opacity=0.8,
            pickable=True,
        ))

    if show_schools:
        s_filt = schools[schools["District"].isin(sel_districts)].copy()
        s_filt["color"] = [[0, 180, 255, 200]] * len(s_filt)   # blue
        s_filt["radius"] = 120
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=s_filt,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            opacity=0.8,
            pickable=True,
        ))

    if show_hospitals:
        h_filt = hosp_df[hosp_df["District"].isin(sel_districts)].copy()
        h_filt["color"] = [[220, 50, 50, 220]] * len(h_filt)   # red
        h_filt["radius"] = 180
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=h_filt,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            opacity=0.8,
            pickable=True,
        ))

    view = pdk.ViewState(latitude=43.24, longitude=76.93, zoom=10.5, pitch=25)

    tooltip = {
        "html": "<b>{Name}</b><br/>{Address}<br/><i>{District}</i>",
        "style": {"background": "#1e1e2e", "color": "white", "borderRadius": "8px", "padding": "8px"},
    }

    if layers:
        theme_mode = st.session_state.get("theme_mode", "light")
        style = "dark" if theme_mode == "dark" else "light"
        st.pydeck_chart(pdk.Deck(
            layers=layers,
            initial_view_state=view,
            tooltip=tooltip,
            map_style=style,
        ))
        st.markdown(
            "🟠 **Kindergartens** &nbsp;&nbsp; 🔵 **Schools** &nbsp;&nbsp; 🔴 **Hospitals**"
        )
    else:
        st.info("Enable at least one layer in the sidebar.")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — District Comparison
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📊 Facility Count by District")

    dist_k = kindergartens[kindergartens["District"].isin(sel_districts)].groupby("District").size().rename("Kindergartens")
    dist_s = schools[schools["District"].isin(sel_districts)].groupby("District").size().rename("Schools")
    dist_h = hosp_df[hosp_df["District"].isin(sel_districts)].groupby("District").size().rename("Hospitals")

    summary = pd.DataFrame([dist_k, dist_s, dist_h]).T.fillna(0).astype(int)
    summary.index.name = "District"
    summary = summary.reset_index()

    if len(summary):
        summary_eval = summary.copy()
        summary_eval["total"] = summary_eval[["Kindergartens", "Schools", "Hospitals"]].sum(axis=1)
        gap_row = summary_eval.sort_values("total", ascending=True).iloc[0]
        risk = severity_bucket(float(gap_row["total"]), 120.0, 220.0)
        render_insight(
            title="Service coverage gap",
            finding=f"{gap_row['District']} has the lowest combined facility count ({int(gap_row['total'])}).",
            action="Prioritize new kindergarten and clinic capacity in this district.",
            risk=risk,
        )

    fig = px.bar(
        summary.melt(id_vars="District", var_name="Type", value_name="Count"),
        x="District",
        y="Count",
        color="Type",
        barmode="group",
        color_discrete_map={"Kindergartens": "#FFA500", "Schools": "#00B4FF", "Hospitals": "#DC3232"},
        labels={"District": "", "Count": "Number of Facilities"},
        title="Facilities per District",
    )
    fig.update_layout(template="plotly_dark", xaxis={"tickangle": -30})
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧒 Kindergartens per District")
        fig_k = px.pie(
            dist_k.reset_index(),
            names="District",
            values="Kindergartens",
            color_discrete_sequence=px.colors.sequential.Oranges_r,
            hole=0.4,
        )
        fig_k.update_layout(template="plotly_dark")
        st.plotly_chart(fig_k, use_container_width=True)

    with col2:
        st.subheader("🎒 Schools per District")
        fig_s = px.pie(
            dist_s.reset_index(),
            names="District",
            values="Schools",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.4,
        )
        fig_s.update_layout(template="plotly_dark")
        st.plotly_chart(fig_s, use_container_width=True)

    st.subheader("📋 Summary Table")
    summary_display = summary.copy()
    summary_display["Total Facilities"] = summary_display[["Kindergartens", "Schools", "Hospitals"]].sum(axis=1)
    summary_display = summary_display.sort_values("Total Facilities", ascending=False).reset_index(drop=True)
    st.dataframe(summary_display, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — Livability Score (combining infrastructure + housing + air quality)
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🏆 District Livability Score")
    st.markdown("""
    This composite score ranks each district based on infrastructure density.
    The score combines **kindergartens**, **schools**, and **hospitals** per district,
    normalized to 0–100. Higher = more facilities relative to other districts.
    
    > 💡 **Tip:** Cross this with housing prices (page 🏠) to find the best value districts!
    """)

    # Build score
    score_df = summary.set_index("District").copy()
    score_df["Total"] = score_df.sum(axis=1)

    max_k = score_df["Kindergartens"].max() or 1
    max_s = score_df["Schools"].max() or 1
    max_h = score_df["Hospitals"].max() or 1

    st.markdown("### Weight controls")
    w_col1, w_col2, w_col3 = st.columns(3)
    with w_col1:
        w_k = st.slider("Kindergartens weight", 0.0, 1.0, 0.35, 0.05)
    with w_col2:
        w_s = st.slider("Schools weight", 0.0, 1.0, 0.35, 0.05)
    with w_col3:
        w_h = st.slider("Hospitals weight", 0.0, 1.0, 0.30, 0.05)

    total_w = max(0.001, w_k + w_s + w_h)
    w_k, w_s, w_h = w_k / total_w, w_s / total_w, w_h / total_w

    score_df["Score"] = (
        (score_df["Kindergartens"] / max_k) * (w_k * 100) +
        (score_df["Schools"]       / max_s) * (w_s * 100) +
        (score_df["Hospitals"]     / max_h) * (w_h * 100)
    ).round(1)

    score_df = score_df.sort_values("Score", ascending=False).reset_index()

    # Gauge-style bar chart
    fig_score = go.Figure()
    colors = ["#00C87A" if s >= 60 else "#FFE600" if s >= 35 else "#DC3232"
              for s in score_df["Score"]]

    fig_score.add_trace(go.Bar(
        x=score_df["District"],
        y=score_df["Score"],
        marker_color=colors,
        text=score_df["Score"].astype(str),
        textposition="outside",
    ))
    fig_score.update_layout(
        template="plotly_dark",
        yaxis=dict(range=[0, 110], title="Infrastructure Score (0–100)"),
        xaxis=dict(title="", tickangle=-25),
        title="District Infrastructure Livability Score",
        showlegend=False,
    )
    st.plotly_chart(fig_score, use_container_width=True)

    st.markdown("🟢 Score ≥ 60 (Great) &nbsp; 🟡 35–60 (Average) &nbsp; 🔴 < 35 (Low infrastructure)")

    # Map view of scores
    st.subheader("🗺️ Score Map")
    map_rows = []
    for _, row in score_df.iterrows():
        d = row["District"]
        if d in DISTRICT_COORDS:
            coords = DISTRICT_COORDS[d]
            norm = row["Score"] / 100
            color = [int(0 + 200 * norm), int(200 * norm), int(150 * (1 - norm)), 190]
            map_rows.append({
                "lat": coords["lat"], "lon": coords["lon"],
                "name_en": DISTRICT_COORDS[d]["name_en"],
                "district": d,
                "score": row["Score"],
                "kindergartens": int(row["Kindergartens"]),
                "schools": int(row["Schools"]),
                "hospitals": int(row["Hospitals"]),
                "color": color,
                "radius": max(1200, int(row["Score"] * 250)),
            })

    if map_rows:
        map_df = pd.DataFrame(map_rows)
        layer = pdk.Layer(
            "ScatterplotLayer", data=map_df,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            opacity=0.75, pickable=True,
        )
        text_layer = pdk.Layer(
            "TextLayer", data=map_df,
            get_position=["lon", "lat"],
            get_text="name_en",
            get_size=14, get_color=[255, 255, 255],
        )
        view2 = pdk.ViewState(latitude=43.25, longitude=76.93, zoom=10, pitch=30)
        tooltip2 = {
            "html": "<b>{district}</b><br/>Score: <b>{score}</b>/100<br/>🧒 {kindergartens} kindergartens<br/>🎒 {schools} schools<br/>🏥 {hospitals} hospitals",
            "style": {"background": "#1e1e2e", "color": "white", "borderRadius": "8px", "padding": "8px"},
        }
        theme_mode = st.session_state.get("theme_mode", "light")
        style = "dark" if theme_mode == "dark" else "light"
        st.pydeck_chart(pdk.Deck(
            layers=[layer, text_layer],
            initial_view_state=view2,
            tooltip=tooltip2,
            map_style=style,
        ))

render_glossary(
    {
        "Livability score": "Normalized weighted score from facility availability.",
        "Coverage gap": "Districts with lowest combined infrastructure access.",
    }
)

render_data_freshness(
    updated_at=max_dataset_mtime([
        "datasets/Almaty_Education_Master.csv",
        "datasets/hospitals_almaty.csv",
    ]),
    source_list=["Almaty_Education_Master.csv", "hospitals_almaty.csv"],
    limitations=[
        "Point-level data does not represent service quality or capacity.",
        "Nearest-centroid hospital district assignment is an approximation.",
    ],
)

render_feedback_widget("Infrastructure")
