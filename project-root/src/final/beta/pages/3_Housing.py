import streamlit as st
import pandas as pd
import re
import pydeck as pdk
import plotly.express as px
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
    DISTRICT_COORDS,
    DISTRICT_KEYWORDS,
)

st.set_page_config(page_title="Housing Prices - Almaty", layout="wide", page_icon="🏠")
apply_base_style()
render_theme_toggle()

# ─── District detection using centralized keywords ──────────────────────────────
def detect_district(address: str) -> str:
    """Detect district from address using centralized DISTRICT_KEYWORDS."""
    if not isinstance(address, str):
        return "Other"
    addr_lower = address.lower()
    for dist, keywords in DISTRICT_KEYWORDS.items():
        for kw in keywords:
            if kw in addr_lower:
                return dist
    # Fallback: check if district name abbreviation is present
    if "р-н" in addr_lower:
        for dist in DISTRICT_COORDS:
            if dist[:4].lower() in addr_lower:
                return dist
    return "Other"

def parse_price(price_str) -> float | None:
    if not isinstance(price_str, str):
        return None
    digits = re.sub(r"[^\d]", "", price_str)
    if not digits:
        return None
    return float(digits)

def parse_area(title: str) -> float | None:
    m = re.search(r"(\d+\.?\d*)\s*м²", title)
    return float(m.group(1)) if m else None

def parse_rooms(title: str) -> str:
    m = re.search(r"(\d+)-комнатная", title)
    return m.group(1) + "-к" if m else "Другое"

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_housing():
    df = pd.read_csv(str(SCRIPT_DIR / "datasets/krisha_final.csv"))
    df["price_num"]  = df["Price"].apply(parse_price)
    df["area_m2"]    = df["Title"].apply(parse_area)
    df["rooms"]      = df["Title"].apply(parse_rooms)
    df["district"]   = df["Address"].apply(detect_district)
    df = df[df["price_num"].notna() & (df["price_num"] > 1_000_000)]
    df["price_M"]    = df["price_num"] / 1_000_000  # millions KZT
    df["price_m2"]   = df["price_num"] / df["area_m2"].replace(0, None)
    return df

try:
    df = load_housing()
except FileNotFoundError:
    st.error("⚠️ Could not find `datasets/krisha_final.csv`. Place the dataset next to the app.")
    st.stop()

# ─── Page header ──────────────────────────────────────────────────────────────
st.title("Housing Prices")
render_page_intro(
    problem="Compare affordability and avoid overpaying in districts with weaker value.",
    how_to_use=[
        "Set budget and room preferences.",
        "Compare district medians and spread.",
        "Use insight box to shortlist value districts.",
    ],
)
st.markdown("Explore apartment listings across Almaty districts.")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")
    price_range = st.slider("Price range (million KZT)",
                            float(df["price_M"].min()), float(df["price_M"].quantile(0.99)),
                            (float(df["price_M"].min()), float(df["price_M"].quantile(0.95))))
    room_opts = sorted(df["rooms"].unique())
    sel_rooms = st.multiselect("Room types", room_opts, default=room_opts)
    available_dists = [d for d in DISTRICT_COORDS.keys() if d in df["district"].unique()]
    sel_dists = st.multiselect("Districts", available_dists,
                                default=available_dists)

common_districts, _ = sidebar_common_filters(
    available_dists, key_prefix="housing"
)
if common_districts:
    sel_dists = [d for d in sel_dists if d in common_districts]

fdf = df[
    (df["price_M"] >= price_range[0]) &
    (df["price_M"] <= price_range[1]) &
    (df["rooms"].isin(sel_rooms)) &
    (df["district"].isin(sel_dists))
]

# ─── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Listings", f"{len(fdf):,}")
c2.metric("Median Price", f"{fdf['price_M'].median():.1f}M ₸")
c3.metric("Avg Area", f"{fdf['area_m2'].mean():.0f} m²" if fdf['area_m2'].notna().any() else "—")
c4.metric("Avg Price/m²", f"{fdf['price_m2'].median()/1000:.0f}K ₸" if fdf['price_m2'].notna().any() else "—")

if len(fdf):
    med_by_dist = fdf.groupby("district")["price_M"].median().sort_values()
    cheapest = med_by_dist.index[0]
    expensive = med_by_dist.index[-1]
    spread = float(med_by_dist.iloc[-1] - med_by_dist.iloc[0])
    risk = severity_bucket(spread, 10.0, 25.0)
    render_insight(
        title="Affordability gap",
        finding=f"Median price gap between {cheapest} and {expensive} is {spread:.1f}M KZT.",
        action="Prioritize districts in the lowest third of median price, then validate infrastructure and safety pages.",
        risk=risk,
    )

st.markdown("---")

# ─── Map ──────────────────────────────────────────────────────────────────────
st.subheader("Average Price by District")

dist_avg = fdf.groupby("district")["price_M"].median().reset_index()
dist_avg.columns = ["district", "median_price"]
price_max = dist_avg["median_price"].max()

map_rows = []
for _, row in dist_avg.iterrows():
    d = row["district"]
    if d in DISTRICT_COORDS:
        info = DISTRICT_COORDS[d]
        norm = row["median_price"] / price_max if price_max > 0 else 0
        color = [int(255 * norm), int(150 * (1 - norm)), 200, 180]
        map_rows.append({
            "lat": info["lat"], "lon": info["lon"],
            "name_en": info["name_en"],
            "district": d,
            "median_price": f"{row['median_price']:.1f}M ₸",
            "color": color,
            "radius": max(1000, int(row["median_price"] * 30000)),
        })

if map_rows:
    map_df = pd.DataFrame(map_rows)
    layer = pdk.Layer("ScatterplotLayer", data=map_df,
                       get_position=["lon", "lat"], get_color="color",
                       get_radius="radius", opacity=0.75, pickable=True)
    text_layer = pdk.Layer("TextLayer", data=map_df,
                            get_position=["lon", "lat"], get_text="name_en",
                            get_size=14, get_color=[255, 255, 255])
    view = pdk.ViewState(latitude=43.25, longitude=76.93, zoom=10, pitch=30)
    tooltip = {
        "html": "<b>{district}</b><br/>Median Price: <b>{median_price}</b>",
        "style": {"background": "#1e1e2e", "color": "white", "borderRadius": "8px", "padding": "8px"}
    }
    theme_mode = st.session_state.get("theme_mode", "light")
    map_style = "dark" if theme_mode == "dark" else "light"
    st.pydeck_chart(pdk.Deck(layers=[layer, text_layer], initial_view_state=view,
                              tooltip=tooltip, map_style=map_style))

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("💰 Price Distribution by District")
    fig = px.box(fdf[fdf["district"] != "Other"], x="district", y="price_M",
                 color="district", labels={"price_M": "Price (million ₸)", "district": ""},
                 title="Price Spread per District")
    fig.update_layout(template="plotly_dark", showlegend=False,
                      xaxis={"tickangle": -30})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🏗️ Price by Room Count")
    fig2 = px.violin(fdf[fdf["rooms"].str.contains(r"\d")], x="rooms", y="price_M",
                     box=True, color="rooms",
                     labels={"price_M": "Price (million ₸)", "rooms": "Room type"})
    fig2.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Sample Listings")
show_cols = ["Title", "Address", "Price", "district", "rooms", "area_m2"]
show_cols = [c for c in show_cols if c in fdf.columns]
st.dataframe(fdf[show_cols].head(50).reset_index(drop=True), use_container_width=True)

render_glossary(
    {
        "Median price": "Middle listing price, robust to outliers.",
        "Price per m2": "Price normalized by area for fairer comparison.",
    }
)

render_data_freshness(
    updated_at=max_dataset_mtime(["datasets/krisha_final.csv"]),
    source_list=["krisha_final.csv"],
    limitations=[
        "District inference is keyword based from address text.",
        "Listings can be duplicated or outdated in scraped sources.",
    ],
)

render_feedback_widget("Housing")

